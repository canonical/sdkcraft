# GitHub Copilot Instructions

This file provides general project context for GitHub Copilot. For Python-specific coding conventions, see [`.github/instructions/python.instructions.md`](instructions/python.instructions.md).

## Project Overview

SDKcraft is a tool that packages and publishes SDKs for [Workshop](https://github.com/canonical/workshop), Canonical's tool for ephemeral development environments. It lets developers define, build, and package complete development toolchains as singular installable units. The project is written in Python, built on the craft-application framework, and distributed as a classic Snap package. Builds and tests run inside LXD (6.6+) containers.

## Tech Stack

- **Language**: Python 3.12+
- **Framework**: craft-application (with craft-cli, craft-parts, craft-platforms, craft-store)
- **Data models**: Pydantic v2
- **Dependency management**: uv (`uv.lock` is committed; `UV_FROZEN=true` by default)
- **Container backend**: LXD (builds and tests run in LXD containers)
- **Packaging**: Snap (core24, classic confinement)
- **Testing**: pytest + pytest-mock (unit/integration) + Spread (e2e in LXD)
- **CI**: GitHub Actions (reusable workflows from `canonical/starflow`)

## Repository Structure

### Core Directories

- `sdkcraft/` — main package
    - `application.py` — `Sdkcraft(Application)` and `APP_METADATA` (default command: `pack`)
    - `cli.py` — entry point; registers services and command groups
    - `commands/` — CLI commands (lifecycle, store, account, docs generation)
    - `models/` — Pydantic models; `models/project.py` defines the `sdkcraft.yaml` schema
    - `services/` — craft-application services (build plan, init, package, project, provider, testing, try)
    - `store/` — SDK Store client
    - `linters/` — interface and shellcheck linters
    - `templates/simple/` — Jinja2 scaffolding used by `sdkcraft init`
    - `doc_templates/` — Jinja2 templates for the generated CLI reference docs
- `tests/` — `unit/` and `integration/` (pytest), `spread/` (e2e suites), `tools/` (Spread helper scripts)
- `snap/` — Snap packaging configuration

### Build Configuration

- `pyproject.toml` / `uv.lock` — project metadata, dependencies, and tool configuration (ruff, mypy, pyright, pytest, codespell)
- `Makefile` — project-specific targets; includes `common.mk`
- `common.mk` — shared Starcraft targets, vendored from `canonical/starbase` — never edit it in this repository
- `spread.yaml` — e2e testing with the Spread framework
- `snap/snapcraft.yaml` — Snap package definition (the snap version is bumped manually here)

### Generated Files (never hand-edit)

- `sdkcraft/_version.py` — written by setuptools_scm from annotated `X.Y.Z` git tags
- CLI reference docs — regenerate with `uv run sdkcraft generate-docs docs/`
- `schema-sdkcraft.json` — regenerate with `uv run python sdkcraft/models/project.py`

## Coding Guidelines

See [`.github/instructions/python.instructions.md`](instructions/python.instructions.md) for detailed Python conventions. Key points:

- **Strict tooling**: ruff (including docstring and type-annotation rules), plus mypy and pyright in strict mode over `sdkcraft/`
- **License header**: every `.py` file starts with the GPL-3 Canonical copyright header
- **Two YAML worlds**: `sdkcraft.yaml` is the SDK definition that the tool consumes (schema in `sdkcraft/models/project.py`); `snap/snapcraft.yaml` is how the tool itself is packaged — do not confuse them

## Common Tasks

### Setting Up

- Run `make setup` to install uv and the full development environment.

### Linting and Formatting

- Run `make lint` for all linters (ruff, codespell, mypy, prettier, pyright, shellcheck, twine, uv lockfile).
- Run `make format` for all automatic formatters.

### Running Tests

- **Unit tests**: `make test-units` (or `uv run pytest tests/unit`)
- **Integration tests**: `make test-integrations` (or `uv run pytest tests/integration`)
- **E2E tests**: Spread suites in `tests/spread/`, excluded from pytest. Example: `spread lxd:ubuntu-24.04:tests/spread/init/`. The `tests/spread/store/` suite is manual and needs store credentials.

### Building and Running Locally

- Run from source with `uv run sdkcraft <command>`.
- Build the snap with `make pack-snap`.

## Available Resources

- **Documentation**: https://ubuntu.com/workshop/docs/ — published docs live in the Workshop documentation site; there is no in-repo `docs/` directory
- **Contributing Guide**: https://ubuntu.com/workshop/docs/contributing/
- **PR Template**: [`.github/PULL_REQUEST_TEMPLATE.md`](PULL_REQUEST_TEMPLATE.md) — description plus documentation checklist

## Related Repositories

These external repositories provide authoritative context for the SDKcraft project:

- https://github.com/canonical/workshop — Workshop, the user-facing product that consumes SDKs built with SDKcraft
- https://github.com/canonical/reference-sdks — reference SDK implementations

## GitHub Actions Workflows

- `qa.yaml` — lint + unit/integration tests (reusable `canonical/starflow` workflows)
- `policy.yaml` — security scanning
- `spread.yaml` — builds the snap (amd64 + arm64), runs Spread e2e tests, publishes to snap channel `edge/<PR#>` on PRs and `edge` on push to main
- `snap.yaml` — manual release: publishes to snap channel `stable`, creates a GitHub release, opens a CLI-reference-docs PR
- `lxd-candidate-check.yaml` — nightly Spread run against the LXD `6/candidate` channel
- `fixup.yaml` — fails if `fixup!`/`squash!` commits remain
- `check-renovate.yaml` — validates `.github/renovate.json5`

## Evolution Note

These instructions are living documentation. When Copilot misbehaves:

1. Note the specific failure mode
2. Identify which instruction file should address it
3. Propose minimal, high-signal edits (avoid essay-style additions)
4. Test with focused prompts before committing changes
