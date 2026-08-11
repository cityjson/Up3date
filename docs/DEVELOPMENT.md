# Development

Up3date supports Python 3.11 and newer and Blender 5.0+'s Python API. Blender
bundles its own Python runtime, which can vary between Blender releases. Check
your Blender version and its bundled Python version before setting up the
development environment. Install the project dependencies with `uv`:

```text
uv sync --dev
```

This synchronizes the project's Python environment and installs the
dependencies needed to build and develop the add-on, including the test,
linting, and type-checking tools. It does not install Blender or install the
add-on into Blender; those are separate prerequisites and steps.

## Quality checks

Run linting, formatting checks, type checking, and unit tests with:

```text
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

To measure test coverage, run:

```text
uv run pytest --cov
```

## Blender integration tests

The integration tests must run inside Blender's Python. Run them from the
repository root with Blender's background executable. Use the command for
your operating system.

### Linux

When `Blender` is on `PATH`:

```bash
blender \
  --background \
  --factory-startup \
  --python-use-system-env \
  --python-exit-code 1 \
  --python tests/blender/run_integration_tests.py
```

### macOS

```bash
/Applications/Blender.app/Contents/MacOS/Blender \
  --background \
  --factory-startup \
  --python-use-system-env \
  --python-exit-code 1 \
  --python tests/blender/run_integration_tests.py
```

### Windows PowerShell

```powershell
& "C:\Program Files\Blender Foundation\Blender\blender.exe" `
  --background `
  --factory-startup `
  --python-use-system-env `
  --python-exit-code 1 `
  --python tests/blender/run_integration_tests.py
```

If Blender is installed elsewhere, replace the executable path. The script
exercises Blender data blocks, add-on registration, and CityJSON import/export
round-trips.

## Visual Studio Code

If you are using `Visual Studio Code`, you may install [Blender Development](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development),
a plugin that allows starting and debugging Python scripts from VS Code.

## Contributing

Clone this repository to develop the add-on and have fun. If you experience a
bug or have a recommendation, open a new issue with all relevant details.
