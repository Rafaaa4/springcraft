# SpringCraft
A Python command-line tool that generates Spring Boot projects using Spring Initializr and can add small local custom templates.

## Requirements
- Python 3.10+
- Internet connection for Spring Initializr generation
- Java and Maven/Gradle only when you want to build/run the generated project

## Install locally
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
springcraft --help
```
