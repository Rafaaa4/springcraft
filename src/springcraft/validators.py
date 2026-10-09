import re
from pathlib import Path

PROJECT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*$")
GROUP_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")

def validate_project_name(value: str) -> str:
    value = value.strip()
    if not PROJECT_RE.fullmatch(value):
        raise ValueError("Project name must start with a letter and contain only letters, digits, or '-'.")
    return value

def validate_group_id(value: str) -> str:
    value = value.strip()
    if not GROUP_RE.fullmatch(value):
        raise ValueError("Group ID must be a dotted Java identifier, e.g. com.example.")
    return value

def validate_package_name(value: str) -> str:
    value = value.strip()
    if not GROUP_RE.fullmatch(value):
        raise ValueError("Package name must be a valid dotted Java package, e.g. com.example.api.")
    return value

def validate_build(value: str) -> str:
    value = value.strip().lower()
    if value not in {"maven", "gradle"}:
        raise ValueError("Build must be either 'maven' or 'gradle'.")
    return value

def validate_destination(path: Path) -> None:
    if path.exists():
        raise ValueError(f"Destination already exists: {path}")
