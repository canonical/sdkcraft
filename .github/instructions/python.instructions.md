---
applyTo: "**/*.py"
description: Python-specific coding conventions for SDKcraft.
---

# Python Code Instructions

## License Header

Every `.py` file starts with the GPL-3 header, followed by a module docstring:

```python
# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""SDKcraft <thing> module."""
```

## Style

- Formatting and linting are enforced by ruff: line length 88, double quotes, LF endings. Run `make format` / `make lint`.
- Docstrings are required (pydocstyle rules) at module, class, and public-function level.
- Full type annotations are required. Use `from __future__ import annotations` and put annotation-only imports under an `if TYPE_CHECKING:` guard.
- Both mypy and pyright run in strict mode over `sdkcraft/`. Tests are exempt from strict typing and docstring rules.
- Mark overridden methods with `@override` (from `typing`).

## Patterns

- CLI commands subclass `craft_application.commands.AppCommand` and are registered in `sdkcraft/cli.py`; user-facing output goes through `craft_cli.emit`.
- Application errors raise `SdkcraftError` (`sdkcraft/errors.py`) or an appropriate craft error with an actionable message.
- Data models use Pydantic v2. The `sdkcraft.yaml` schema lives in `sdkcraft/models/project.py`; constrained field types live in `sdkcraft/models/constraints.py`.
- Services subclass craft-application services and are registered in `sdkcraft/services/__init__.py`.

## Testing

- Unit tests live in `tests/unit/`, mirroring the package layout; integration tests in `tests/integration/`.
- Shared fixtures live in `tests/conftest.py`, built on craft-application's `ServiceFactory`.
- Mock with `pytest-mock` (the `mocker` fixture).
- Mark slow tests with `@pytest.mark.slow`; `xfail_strict` is enabled.
- End-to-end scenarios are Spread suites under `tests/spread/` (excluded from pytest), with helper scripts in `tests/tools/`.

## Gold Standard Examples

- CLI command: [`sdkcraft/commands/create_track.py`](../../sdkcraft/commands/create_track.py)
- Service registration: [`sdkcraft/services/__init__.py`](../../sdkcraft/services/__init__.py)
- Model with validation: [`sdkcraft/models/project.py`](../../sdkcraft/models/project.py)
- Unit test: [`tests/unit/commands/test_create_track.py`](../../tests/unit/commands/test_create_track.py)
