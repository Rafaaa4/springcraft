from pathlib import Path
from jinja2 import Environment, StrictUndefined

TEMPLATES = {
    "hello": "Adds a simple REST controller at /api/hello.",
}

def list_templates() -> list[tuple[str, str]]:
    return sorted(TEMPLATES.items())

def apply_template(template_name: str | None, project_dir: Path, package_name: str) -> list[Path]:
    if not template_name:
        return []
    if template_name not in TEMPLATES:
        known = ", ".join(sorted(TEMPLATES))
        raise ValueError(f"Unknown template '{template_name}'. Available templates: {known}")

    env = Environment(undefined=StrictUndefined, autoescape=False, keep_trailing_newline=True)
    package_path = Path(*package_name.split("."))
    java_dir = project_dir / "src" / "main" / "java" / package_path
    java_dir.mkdir(parents=True, exist_ok=True)

    source = r"""package {{ package_name }};

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {

    @GetMapping("/api/hello")
    public String hello() {
        return "Hello from SpringCraft!";
    }
}
"""
    rendered = env.from_string(source).render(package_name=package_name)
    target = java_dir / "HelloController.java"
    target.write_text(rendered, encoding="utf-8")
    return [target]
