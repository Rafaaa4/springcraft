# SpringCraft
A Python command-line tool that generates Spring Boot projects using Spring Initializr and can add small local custom templates.

## Requirements
- Python 3.10+
- Internet connection for Spring Initializr generation
- Java and Maven/Gradle only when you want to build/run the generated project

## Install Globally

The best way to install SpringCraft and use it from anywhere on any OS (Windows, Mac, Linux) is using `pipx` (which isolates dependencies) or `pip`.

### Option 1: Install directly from GitHub using pipx (Recommended)
```bash
pipx install git+https://github.com/Rafaaa4/springcraft.git
```

### Option 2: Install directly from GitHub using pip
```bash
pip install git+https://github.com/Rafaaa4/springcraft.git
```

Once installed, you can run the tool from anywhere in your terminal:
```bash
springcraft create
```

## Usage

Here are the available commands you can use with SpringCraft:

### 1. View Help
To see all available commands and options:
```bash
springcraft --help
```

### 2. Create a Project Interactively
To start the interactive wizard and create a new Spring Boot project:
```bash
springcraft create
```

### 3. Check Available Dependencies
To list all Spring Initializr dependencies you can use:
```bash
springcraft dependencies
```

### 4. View Available Custom Templates
To see the custom local templates included in the CLI (e.g., hello template):
```bash
springcraft templates
```

### 5. Check System Tools
To verify that you have Java, Maven, Gradle, and Python properly installed:
```bash
springcraft doctor
```
