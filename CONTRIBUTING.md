# Contributing

## Application Entry Point

The main application entry point is `manta_airfoil_tools.py`.
On Windows, use `manta_airfoil_tools.bat`.

## Release Build

To package the executable with PyInstaller, use:

```bash
python release_tool/release_tool.py build
```

To clean generated artifacts:

```bash
python release_tool/release_tool.py clean
```

More details are available in `release_tool/README.md`.

## Licensing of Contributions

By contributing to this repository, you agree that your contributions will be released under:

- GPL-3.0-only

This keeps the contribution terms aligned with the repository license.

## Project Credit

Project credit should remain visible in repository-facing materials:

- Manta AirLab — Airfoil Tools by Fabio Giuliodori
- https://duilio.cc

## Pull Request Guidelines

- Keep changes small and focused.
- Include a clear summary of what changed and why.
- Add verification steps/commands in the PR description.
- Update documentation when behavior or usage changes.

## Local checks

Run these before opening a PR:

```bash
python -m py_compile manta_airfoil_tools.py airfoil_library.py release_tool/release_tool.py
python -c "import airfoil_library; print('OK')"
python manta_airfoil_tools.py --help
python manta_airfoil_tools.py export --help
python manta_airfoil_tools.py analyze --help
python benchmarks/compare_cli_vs_reference.py --case benchmarks/cases/naca0012_case.json
```
