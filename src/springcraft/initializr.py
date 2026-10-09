from __future__ import annotations
import io
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import httpx

INITIALIZR_URL = "https://start.spring.io"
TIMEOUT = 30.0

class InitializrError(RuntimeError):
    """Raised when Spring Initializr cannot generate a project."""

def fetch_metadata(client: httpx.Client | None = None) -> dict[str, Any]:
    owns_client = client is None
    client = client or httpx.Client(timeout=TIMEOUT, follow_redirects=True)
    try:
        response = client.get(f"{INITIALIZR_URL}/metadata/client")
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise InitializrError("Spring Initializr returned unexpected metadata.")
        return data
    except (httpx.HTTPError, ValueError) as exc:
        raise InitializrError(f"Could not fetch Spring Initializr metadata: {exc}") from exc
    finally:
        if owns_client:
            client.close()

def _field(metadata: dict[str, Any], name: str) -> dict[str, Any]:
    field = metadata.get(name)
    if isinstance(field, dict):
        return field
    return {}

def default_boot_version(metadata: dict[str, Any]) -> str:
    field = _field(metadata, "bootVersion")
    default = field.get("default")
    if isinstance(default, str) and default:
        return default
    values = field.get("values", [])
    for item in values:
        if isinstance(item, dict) and item.get("default") is True:
            value = item.get("id")
            if value:
                return str(value)
    if values and isinstance(values[0], dict) and values[0].get("id"):
        return str(values[0]["id"])
    raise InitializrError("Could not determine the default Spring Boot version from metadata.")

def available_dependency_ids(metadata: dict[str, Any]) -> set[str]:
    field = _field(metadata, "dependencies")
    result: set[str] = set()
    for item in field.get("values", []):
        if not isinstance(item, dict):
            continue
        for dep in item.get("values", []):
            if isinstance(dep, dict) and dep.get("id"):
                result.add(str(dep["id"]))
    return result

def generate_project(
    destination: Path,
    *,
    project_name: str,
    build: str,
    group_id: str,
    package_name: str,
    java_version: str,
    dependencies: list[str],
    language: str = "java",
    packaging: str = "jar",
    boot_version: str | None = None,
    client: httpx.Client | None = None,
) -> Path:
    metadata = fetch_metadata(client)
    chosen_boot_version = boot_version or default_boot_version(metadata)
    allowed = available_dependency_ids(metadata)
    unknown = sorted(set(dependencies) - allowed)
    if unknown:
        raise InitializrError(
            "Unknown dependency ID(s): " + ", ".join(unknown) + ". Run 'springcraft dependencies' to inspect supported IDs."
        )

    params = {
        "type": build,
        "language": language,
        "bootVersion": chosen_boot_version,
        "baseDir": project_name,
        "groupId": group_id,
        "artifactId": project_name.lower().replace("_", "-"),
        "name": project_name,
        "packageName": package_name,
        "packaging": packaging,
        "javaVersion": java_version,
        "dependencies": ",".join(dependencies),
    }

    owns_client = client is None
    client = client or httpx.Client(timeout=TIMEOUT, follow_redirects=True)
    try:
        response = client.get(f"{INITIALIZR_URL}/starter.zip", params=params)
        if response.status_code >= 400:
            detail = response.text[:500].strip()
            raise InitializrError(f"Spring Initializr rejected the request (HTTP {response.status_code}). {detail}")
        content_type = response.headers.get("content-type", "")
        if "zip" not in content_type.lower() and not response.content.startswith(b"PK\x03\x04"):
            raise InitializrError("Spring Initializr did not return a ZIP file. Check the selected options.")

        destination.mkdir(parents=True, exist_ok=False)
        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                _safe_extract(archive, destination)
        except (zipfile.BadZipFile, OSError, ValueError) as exc:
            raise InitializrError(f"Could not extract generated project: {exc}") from exc
        return destination
    except httpx.HTTPError as exc:
        raise InitializrError(f"Could not contact Spring Initializr: {exc}") from exc
    finally:
        if owns_client:
            client.close()

def _safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for member in archive.infolist():
        member_path = PurePosixPath(member.filename)
        if member_path.is_absolute() or ".." in member_path.parts:
            raise ValueError(f"Unsafe path in downloaded ZIP: {member.filename}")
        target = (destination / Path(*member_path.parts)).resolve()
        if target != root and root not in target.parents:
            raise ValueError(f"Unsafe path in downloaded ZIP: {member.filename}")
        archive.extractall(destination)
