from pathlib import Path
import pytest
from springcraft.validators import (
    validate_build,
    validate_destination,
    validate_group_id,
    validate_package_name,
    validate_project_name,
)

def test_valid_project_name():
    assert validate_project_name("my-api_2") == "my-api_2"

@pytest.mark.parametrize("name", ["", "../api", "2api", "my api", "api/../bad"])
def test_invalid_project_name(name):
    with pytest.raises(ValueError):
        validate_project_name(name)

def test_valid_group_and_package():
    assert validate_group_id("com.example") == "com.example"
    assert validate_package_name("com.example.api") == "com.example.api"

@pytest.mark.parametrize("value", ["com..example", "com.example-", "not a package", ""])
def test_invalid_group_or_package(value):
    with pytest.raises(ValueError):
        validate_group_id(value)

def test_build():
    assert validate_build("MAVEN") == "maven"
    assert validate_build("gradle") == "gradle"
    with pytest.raises(ValueError):
        validate_build("ant")

def test_destination_must_not_exist(tmp_path: Path):
    with pytest.raises(ValueError):
        validate_destination(tmp_path)
