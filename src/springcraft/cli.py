from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
import sys

import httpx
import questionary
import typer
from rich.console import Console
from rich.table import Table

from springcraft.initializr import (
    InitializrError,
    available_dependency_ids,
    default_boot_version,
    fetch_metadata,
    generate_project,
)
from springcraft.templates import apply_template, list_templates
from springcraft.validators import (
    validate_destination,
    validate_group_id,
    validate_package_name,
    validate_project_name,
)

app = typer.Typer(
    name="springcraft",
    help="Generate Spring Boot projects from your terminal.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
console = Console()

def _parse_dependencies(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]

@app.command()
def create(
    output: Path = typer.Option(Path("."), "--output", "-o", help="Parent directory for the project."),
) -> None:
    """Create a new Spring Boot project interactively."""
    try:
        console.print("[bold]Fetching Spring Initializr metadata...[/bold]")
        metadata = fetch_metadata()

        # Parse choices from metadata
        boot_versions = [(v['id'], v['name']) for v in metadata.get('bootVersion', {}).get('values', [])]
        java_versions = [(v['id'], v['name']) for v in metadata.get('javaVersion', {}).get('values', [])]
        languages = [(v['id'], v['name']) for v in metadata.get('language', {}).get('values', [])]
        packagings = [(v['id'], v['name']) for v in metadata.get('packaging', {}).get('values', [])]
        build_types = [(v['id'], v['name']) for v in metadata.get('type', {}).get('values', []) if v['action'] == '/starter.zip']
        
        all_deps = []
        for category in metadata.get('dependencies', {}).get('values', []):
            for dep in category.get('values', []):
                all_deps.append(questionary.Choice(title=f"{dep['name']} ({category['name']}) - {dep.get('description', '')}", value=dep['id']))

        # Project type
        build = questionary.select(
            "Project Type:",
            choices=[questionary.Choice(title=n, value=i) for i, n in build_types]
        ).ask()
        if not build: raise typer.Abort()

        # Language
        language = questionary.select(
            "Language:",
            choices=[questionary.Choice(title=n, value=i) for i, n in languages]
        ).ask()
        if not language: raise typer.Abort()

        # Spring Boot Version
        boot_version = questionary.select(
            "Spring Boot Version:",
            choices=[questionary.Choice(title=n, value=i) for i, n in boot_versions]
        ).ask()
        if not boot_version: raise typer.Abort()

        # Project metadata
        group_id = questionary.text("Group:", default="com.example").ask()
        if not group_id: raise typer.Abort()
        group_id = validate_group_id(group_id)

        project_name = questionary.text("Artifact:", default="demo").ask()
        if not project_name: raise typer.Abort()
        project_name = validate_project_name(project_name)

        package_name = questionary.text("Package name:", default=f"{group_id}.{project_name.lower().replace('-', '').replace('_', '')}").ask()
        if not package_name: raise typer.Abort()
        package_name = validate_package_name(package_name)

        packaging = questionary.select(
            "Packaging:",
            choices=[questionary.Choice(title=n, value=i) for i, n in packagings]
        ).ask()
        if not packaging: raise typer.Abort()

        java_version = questionary.select(
            "Java Version:",
            choices=[questionary.Choice(title=n, value=i) for i, n in java_versions]
        ).ask()
        if not java_version: raise typer.Abort()

        # Dependencies
        dependencies = questionary.checkbox(
            "Select Dependencies (use Space to select, Enter to confirm):",
            choices=all_deps
        ).ask()
        if dependencies is None: raise typer.Abort()

        # Template
        template = questionary.select(
            "Add a custom template?",
            choices=["none", "hello"],
            default="none",
        ).ask()
        if template == "none":
            template = None
        if not template and template != None: raise typer.Abort()

        validate_destination(output / project_name)

        destination = generate_project(
            output / project_name,
            project_name=project_name,
            build=build,
            group_id=group_id,
            package_name=package_name,
            java_version=java_version,
            dependencies=dependencies,
            language=language,
            packaging=packaging,
            boot_version=boot_version,
        )

        added = apply_template(template, destination, package_name)

        console.print(f"\n[green]Project created:[/green] {destination.resolve()}")
        if added:
            for path in added:
                console.print(f"[green]Added template file:[/green] {path.relative_to(destination)}")

        console.print("\nNext steps:")
        console.print(f"  cd {destination}")
        if "maven" in build:
            console.print("  ./mvnw spring-boot:run")
        else:
            console.print("  ./gradlew bootRun")

    except (ValueError, InitializrError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

@app.command()
def dependencies() -> None:
    """List dependency IDs currently available from Spring Initializr."""
    try:
        metadata = fetch_metadata()
        ids = sorted(available_dependency_ids(metadata))
        table = Table("Dependency ID", title="Spring Initializr dependencies")
        for item in ids:
            table.add_row(item)
        console.print(table)
    except InitializrError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

@app.command()
def templates() -> None:
    """List built-in custom templates."""
    table = Table("Template", "Description", title="SpringCraft templates")
    for name, description in list_templates():
        table.add_row(name, description)
    console.print(table)

@app.command()
def doctor() -> None:
    """Check local tools commonly needed to build generated projects."""
    checks = {
        "Python": [sys.executable, "--version"],
        "Java": ["java", "-version"],
        "Maven": ["mvn", "-version"],
        "Gradle": ["gradle", "-version"],
    }

    for label, command in checks.items():
        executable = command[0]
        if executable != sys.executable and shutil.which(executable) is None:
            console.print(f"[yellow]MISSING[/yellow] {label}: not found in PATH")
            continue
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False)
            output = (result.stdout or result.stderr).strip().splitlines()
            first_line = output[0] if output else "available"
            status = "[green]OK[/green]" if result.returncode == 0 else "[yellow]CHECK[/yellow]"
            console.print(f"{status}  {label}: {first_line}")
        except (OSError, subprocess.TimeoutExpired) as exc:
            console.print(f"[yellow]CHECK[/yellow]  {label}: {exc}")

if __name__ == "__main__":
    app()
