from pathlib import Path
from springcraft.templates import apply_template, list_templates

def test_hello_template_creates_controller(tmp_path: Path):
    created = apply_template("hello", tmp_path, "com.example.demo")
    assert len(created) == 1
    target = tmp_path / "src/main/java/com/example/demo/HelloController.java"
    assert target.exists()
    text = target.read_text(encoding="utf-8")
    assert "package com.example.demo;" in text
    assert '@GetMapping("/api/hello")' in text

def test_no_template_is_noop(tmp_path: Path):
    assert apply_template(None, tmp_path, "com.example.demo") == []

def test_template_list():
    assert any(name == "hello" for name, _ in list_templates())
