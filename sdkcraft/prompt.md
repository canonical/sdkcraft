# Complete Agentic Prompt for Adding Linting Substep to SDKcraft Pack

## Context & Requirements

### Goal

Add a linting substep to the 'pack' step in sdkcraft that runs shellcheck on scripts in the `hooks/` directory, with configurable ignore functionality via `lint.ignore` in `sdkcraft.yaml`.

### Clarified Requirements

- **Linter Integration**: Add shellcheck to snap dependencies AND allow users to specify linters via config (B+C)
- **Configuration**: Manual specification (no automatic detection)
- **Lint Scope**: All scripts in the `hooks/` directory only
- **Failure Behavior**:
    - Errors (shellcheck severity=error) → Stop packing immediately (fail fast)
    - All other severities (warning, info, style) → Show warnings but continue packing
- **Initial Linters**: shellcheck only

## Codebase Architecture (from exploration)

### Key Files & Locations

#### Pack Command

`/home/runner/work/sdkcraft/sdkcraft/sdkcraft/commands/lifecycle.py` (line 49)

- `PackCommand` extends `craft_application.commands.lifecycle.PackCommand`
- Override `_run()` method to inject linting substep
- Access services via `self._services.get("service_name")`
- Use `emit.progress()` for user messages

#### Package Service

`/home/runner/work/sdkcraft/sdkcraft/sdkcraft/services/package.py`

- `pack()` method (lines 52-88) creates `.sdk` tarball
- `write_metadata()` (lines 128-145) writes `meta/sdk.yaml` and copies hooks
- Hooks are copied from `dirs.project_dir / "hooks"` to `prime_dir / "sdk" / "hooks"`

#### Project Model

`/home/runner/work/sdkcraft/sdkcraft/sdkcraft/models/project.py`

- Line 222: `class Project(models.Project)` - add `lint` field here
- Uses Pydantic models for validation
- See examples: `Plugs` (line 189), `Slots` (line 194)

#### Snap Packaging

`/home/runner/work/sdkcraft/sdkcraft/snap/snapcraft.yaml`

- Add shellcheck to `stage-packages` in `sdkcraft-libs` part (lines 27-40)

### Existing Patterns

- **Validation**: Raise `CraftValidationError` for failures (see line 204 in lifecycle.py)
- **Progress Messages**: Use `emit.progress("message", permanent=True/False)` (see line 151)
- **Service Access**: `self._services.get("lifecycle").project_info.dirs` (line 66)
- **Command Override**: See `TryCommand._run()` (line 118) for pattern

## Implementation Steps

### Step 1: Add shellcheck to Snap Dependencies

**File**: `/home/runner/work/sdkcraft/sdkcraft/snap/snapcraft.yaml`

Add shellcheck to the `stage-packages` list in the `sdkcraft-libs` part (around line 28-40):

```yaml
parts:
    sdkcraft-libs:
        stage-packages:
            - shellcheck # ADD THIS LINE
            - apt
            - apt-transport-https
            # ... rest of packages
```

### Step 2: Add Lint Configuration Model

**File**: `/home/runner/work/sdkcraft/sdkcraft/sdkcraft/models/project.py`

Add after line 217 (before `class Project`):

```python
class LintIgnore(models.CraftBaseModel):
    """Lint ignore configuration for a specific linter."""

    shellcheck: list[str] = []  # e.g., ["warning", "info", "style"]


class LintConfig(models.CraftBaseModel):
    """SDKcraft lint configuration."""

    ignore: LintIgnore = LintIgnore()
```

Then add to `class Project` (around line 222):

```python
class Project(models.Project):
    """SDKcraft project definition."""

    name: ProjectName

    lint: LintConfig = LintConfig()  # ADD THIS LINE
    plugs: Plugs = {}
    slots: Slots = {}
    parts: dict[str, Part] = DEFAULT_PART
```

### Step 3: Create Linting Function

**File**: `/home/runner/work/sdkcraft/sdkcraft/sdkcraft/commands/lifecycle.py`

Add imports at top (around line 25):

```python
from pathlib import Path
import json
from craft_cli import emit, CraftError
```

Add new function before `PackCommand` class (around line 45):

```python
def _run_shellcheck_on_hooks(hooks_dir: Path, ignore_severities: list[str]) -> None:
    """Run shellcheck on all scripts in hooks directory.

    :param hooks_dir: Path to hooks directory
    :param ignore_severities: List of severities to ignore (e.g., ["warning", "info"])
    :raises CraftError: If shellcheck finds errors (severity=error)
    """
    if not hooks_dir.is_dir():
        return  # No hooks directory, nothing to lint

    # Find all files in hooks directory (scripts are typically non-.yaml files)
    script_files = [
        f for f in hooks_dir.iterdir()
        if f.is_file() and not f.is_symlink() and not f.suffix in ['.yaml', '.md']
    ]

    if not script_files:
        return  # No scripts to lint

    emit.progress("Linting hooks with shellcheck...")

    has_errors = False
    warnings = []

    for script in script_files:
        # Run shellcheck with JSON output for easier parsing
        result = subprocess.run(
            ["shellcheck", "--format=json", str(script)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            continue  # No issues found

        try:
            issues = json.loads(result.stdout)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            emit.message(f"Warning: Could not parse shellcheck output for {script.name}")
            continue

        # Filter issues based on ignore configuration
        for issue in issues:
            severity = issue.get("level", "").lower()

            if severity in ignore_severities:
                continue  # Ignored severity

            # Format issue message
            line = issue.get("line", "?")
            col = issue.get("column", "?")
            code = issue.get("code", "")
            message = issue.get("message", "")

            issue_msg = f"{script.name}:{line}:{col}: [{severity}] {message} (SC{code})"

            if severity == "error":
                emit.message(issue_msg, intermediate=True)
                has_errors = True
            else:
                warnings.append(issue_msg)

    # Display warnings
    if warnings:
        emit.progress("Shellcheck warnings:", permanent=True)
        for warning in warnings:
            emit.message(warning, intermediate=True)

    # Fail if errors were found
    if has_errors:
        raise CraftError(
            "Shellcheck found errors in hooks scripts.",
            resolution="Fix the errors reported above or add them to 'lint.ignore.shellcheck' in sdkcraft.yaml"
        )

    emit.progress("Linting completed successfully.", permanent=True)
```

### Step 4: Integrate Linting into PackCommand

**File**: `/home/runner/work/sdkcraft/sdkcraft/sdkcraft/commands/lifecycle.py`

Modify the `PackCommand` class (starting at line 49):

```python
class PackCommand(lifecycle.PackCommand):
    """Command to pack the final artifact."""

    @override
    def _run(
        self, parsed_args: Namespace, step_name: str | None = None, **kwargs: Any
    ) -> None:
        """Run the pack command with linting substep."""
        # Run the standard lifecycle up to prime
        super()._run(parsed_args=parsed_args, step_name=step_name, **kwargs)

        # Run linting substep before packing (only if we're at pack step)
        if step_name is None or step_name == "pack":
            self._lint_hooks()

    def _lint_hooks(self) -> None:
        """Run shellcheck linting on hooks directory."""
        dirs = self._services.get("lifecycle").project_info.dirs
        hooks_dir = dirs.project_dir / "hooks"

        # Get ignore configuration from project
        ignore_severities = self._project.lint.ignore.shellcheck

        # Run shellcheck
        _run_shellcheck_on_hooks(hooks_dir, ignore_severities)

    @override
    def _is_already_packed(self) -> bool:
        # ... existing code remains unchanged
```

### Step 5: Add Tests

#### Unit Tests

**File**: Create `/home/runner/work/sdkcraft/sdkcraft/tests/unit/commands/test_lint.py`

```python
"""Tests for linting functionality in pack command."""

from pathlib import Path
import pytest
from sdkcraft.commands.lifecycle import _run_shellcheck_on_hooks
from craft_cli import CraftError


def test_lint_no_hooks_dir(tmp_path):
    """Test linting when hooks directory doesn't exist."""
    hooks_dir = tmp_path / "hooks"
    # Should not raise
    _run_shellcheck_on_hooks(hooks_dir, [])


def test_lint_empty_hooks_dir(tmp_path):
    """Test linting when hooks directory is empty."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    # Should not raise
    _run_shellcheck_on_hooks(hooks_dir, [])


def test_lint_valid_script(tmp_path):
    """Test linting with valid shell script."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()

    script = hooks_dir / "setup-base"
    script.write_text("#!/bin/bash\necho 'Hello'\n")

    # Should not raise
    _run_shellcheck_on_hooks(hooks_dir, [])


def test_lint_script_with_warning(tmp_path):
    """Test linting with script that has warnings."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()

    script = hooks_dir / "setup-base"
    # Script with unquoted variable (shellcheck warning)
    script.write_text("#!/bin/bash\necho $VAR\n")

    # Should not raise (warnings are non-fatal)
    _run_shellcheck_on_hooks(hooks_dir, [])


def test_lint_script_with_ignored_warning(tmp_path):
    """Test linting with ignored warning severity."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()

    script = hooks_dir / "setup-base"
    script.write_text("#!/bin/bash\necho $VAR\n")

    # Should not raise (warnings ignored)
    _run_shellcheck_on_hooks(hooks_dir, ["warning"])
```

**File**: Add to `/home/runner/work/sdkcraft/sdkcraft/tests/unit/models/test_project.py`

Add test for lint configuration:

```python
def test_project_with_lint_config():
    """Test project with lint ignore configuration."""
    project_data = {
        "name": "test-sdk",
        "version": "1.0",
        "summary": "Test",
        "description": "Test SDK",
        "base": "ubuntu@22.04",
        "lint": {
            "ignore": {
                "shellcheck": ["warning", "info", "style"]
            }
        }
    }
    project = Project.unmarshal(project_data)
    assert project.lint.ignore.shellcheck == ["warning", "info", "style"]


def test_project_default_lint_config():
    """Test project with default (empty) lint config."""
    project_data = {
        "name": "test-sdk",
        "version": "1.0",
        "summary": "Test",
        "description": "Test SDK",
        "base": "ubuntu@22.04",
    }
    project = Project.unmarshal(project_data)
    assert project.lint.ignore.shellcheck == []
```

#### Integration Test

**File**: Create `/home/runner/work/sdkcraft/sdkcraft/tests/spread/lint-hooks/task.yaml`

```yaml
summary: Test shellcheck linting on hooks

prepare: |
  run_sdkcraft init

restore: |
  run_sdkcraft clean || true

execute: |
  # Test 1: Valid hooks should pass
  mkdir -p hooks
  cat > hooks/setup-base << 'EOF'
#!/bin/bash
echo "Valid script"
EOF

  run_sdkcraft pack
  echo "Test 1 passed: Valid hooks"

  # Clean up
  run_sdkcraft clean

  # Test 2: Hooks with warnings should pass (with warnings shown)
  cat > hooks/setup-base << 'EOF'
#!/bin/bash
echo $UNQUOTED
EOF

  run_sdkcraft pack
  echo "Test 2 passed: Warnings don't fail"

  # Clean up
  run_sdkcraft clean

  # Test 3: Ignore warnings in config
  cat > sdkcraft.yaml << 'EOF'
name: my-sdk-name
base: ubuntu@22.04
version: "0.1"
summary: Test SDK
description: Test
lint:
  ignore:
    shellcheck:
      - warning
      - info
      - style
EOF

  run_sdkcraft pack
  echo "Test 3 passed: Ignored warnings"
```

**File**: Create `/home/runner/work/sdkcraft/sdkcraft/tests/spread/lint-hooks/sdkcraft.yaml`

```yaml
name: my-sdk-name
base: ubuntu@22.04
version: "0.1"
summary: Test linting
description: Test SDK for linting functionality
```

### Step 6: Update Documentation (Optional but Recommended)

**File**: Consider adding to `README.rst` or creating `docs/linting.md`

```rst
Linting
-------

SDKcraft automatically runs shellcheck on scripts in the ``hooks/`` directory
during the pack step. This helps catch common shell scripting errors early.

To ignore specific shellcheck severity levels, add to your ``sdkcraft.yaml``::

    lint:
      ignore:
        shellcheck:
          - warning
          - info
          - style

By default, only errors will cause the pack to fail. Warnings, info, and style
issues are displayed but don't prevent packing.
```

## Testing & Validation

### Manual Testing Steps

1. **Install dependencies**: Ensure shellcheck is available in snap
2. **Test valid script**: Create SDK with valid hooks, run `sdkcraft pack`
3. **Test with warnings**: Create hook with unquoted variables, verify warnings shown but pack succeeds
4. **Test with errors**: Create hook with syntax errors, verify pack fails
5. **Test ignore config**: Add `lint.ignore.shellcheck` to yaml, verify warnings are suppressed
6. **Test no hooks**: Project without hooks directory should work normally

### Run Tests

```bash
# Unit tests
uv run pytest tests/unit/commands/test_lint.py
uv run pytest tests/unit/models/test_project.py -k lint

# Integration tests (if spread available)
# spread tests/spread/lint-hooks
```

## Success Criteria

- [ ] shellcheck added to snap dependencies
- [ ] lint configuration model added to Project schema
- [ ] Linting function implemented with severity filtering
- [ ] PackCommand integrates linting substep before pack
- [ ] Error severity causes pack failure
- [ ] Warning/info/style severities show messages but continue
- [ ] `lint.ignore.shellcheck` configuration works correctly
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing confirms expected behavior
- [ ] Linting only runs on `hooks/` directory scripts
- [ ] No hooks directory doesn't cause errors

## Notes & Considerations

- **Performance**: Linting adds ~1-2 seconds to pack time (acceptable)
- **Extensibility**: Design allows adding more linters (yamllint, etc.) in future
- **User Experience**: Clear error messages with resolution hints
- **Backward Compatibility**: Default empty ignore list maintains current behavior
- **Edge Cases**: Handle missing shellcheck gracefully (in case snap build fails)
