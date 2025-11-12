# AI Coding Agent Quick Reference for Difflex

This document provides a quick reference for AI coding agents working on the Difflex project. For comprehensive architecture details, see [.github/copilot-instructions.md](.github/copilot-instructions.md).

## Quick Start for Agents

### Agent Mode of Operation

**Autonomy First**: You are an autonomous coding agent. Execute tasks to completion without asking for permission. Only yield back to the user when the problem is fully solved.

**Context Strategy**: Parallelize searches, deduplicate paths, stop as soon as you can act (when you can name exact content to change, or top hits converge ~70% on one area).

**Quality Bar**: Internally create a 5-7 category rubric for what makes a world-class solution. Iterate until your response hits top marks in all categories. Do not show this rubric to the user.

## Critical Project Constraints

### Code Standards (Strict)

- **Black formatter**: Max line length 160 (`pyproject.toml`)
- **Pylint**: Max args=10, locals=25, branches=20, statements=60
- **No environment-dependent characters** in code/comments (ASCII only for code)
- **All user-facing strings**: Use `tr("key_name")` from `utils.i18n`
- **Paths**: Always use `pathlib.Path` for cross-platform compatibility

## Project Overview

Difflex is a cross-platform (Windows/macOS/Linux) GUI file and directory comparison tool built with **PySide6**. It delegates actual diff visualization to external tools while handling comparison logic, similarity detection, and workflow orchestration internally.

### Key Architecture Components

- **Entry Point**: `src/difflex/main.py` - Initializes Qt app, i18n system, and main window
- **UI Layer**: `src/difflex/modules/` - Tab-based UI with home screen, comparison widgets, and settings
- **Comparison Engine**: `src/difflex/utils/comparator.py` - Three comparator classes (Text, Image, Binary)
- **Settings & i18n**: `utils/settings.py` (QSettings-based) and `utils/i18n.py` (JSON-based translations)

### Comparison Result Symbols

- `=` Identical
- `≒` Similar (within threshold)
- `≒EX` Similar except EXIF metadata
- `≠` Different

## Development Workflow

### Setup

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install with dev dependencies
pip install -e ".[dev]"
```

### Build Executable

```powershell
# Windows (uses Nuitka)
.\build_windows.ps1  # Creates standalone .exe with app.ico
```

## Project-Specific Patterns

### External Tool Integration

Settings store per-file-type (text/image/binary) tool configurations with `%s` placeholders:

```python
{
    "executable": "C:/path/to/diff.exe",
    "arg_before": "--mode=side-by-side",
    "arg1": "%s",  # Placeholder for file1
    "arg2": "%s",  # Placeholder for file2
    "arg3": "%s",  # Placeholder for file3
    "arg_after": "",
    "pack_args": True  # Removes gaps when comparing 2 of 3 files
}
```

### Multi-Encoding Text Handling

`TextComparator.compare()` attempts UTF-8, UTF-8-sig, Shift-JIS, CP932, Latin-1 in sequence to handle diverse source files (Japanese project).

### Background Comparison Architecture

`DirectoryComparisonWorker` emits three signal types:

- `progress(current, total, message)` - Update progress bar
- `file_found(FileComparisonItem)` - Add item to UI immediately
- `comparison_complete(item, results)` - Update item with comparison results

Workers can be stopped mid-execution via `worker.stop()` - app remains responsive during long comparisons.

### Translation Workflow

1. Add keys to `locales/en-US.json` and `locales/ja-JP.json`
2. Use `tr("key_name")` in UI code
3. Auto-detects system locale on first run; user can override in settings

## Key Files Reference

- **Comparison logic**: `utils/comparator.py` - `ComparisonResult` class and three comparator implementations
- **Settings schema**: `utils/settings.py` - All persistent config keys and defaults
- **Worker pattern**: `modules/comparison_worker.py` - Template for background processing
- **External tool launching**: `modules/file_comparison_widget.py` - See `_launch_external_tool()` method
- **Requirements doc**: `Documents/ファイル比較アプリ要件定義.md` - Original Japanese spec (authoritative for feature disputes)

## Agent Workflow: Step-by-Step

### 1. Context Gathering Phase

**DO**:

- Run parallel searches with varied queries (semantic_search, grep_search, file_search)
- Read top 2-3 hits per query
- Deduplicate paths and cache results
- Stop as soon as you can name exact content to change (~70% signal convergence)

**DON'T**:

- Repeat the same query
- Read entire codebase when top hits converge
- Over-search for "completeness"

### 2. Planning Phase (Internal - Not Shown to User)

**DO**:

- Create 5-7 category rubric for world-class solution (readability, maintainability, consistency, visual quality, performance, error handling, i18n)
- Identify exact files and functions to modify
- Plan minimal batch of changes

**DON'T**:

- Show rubric to user
- Ask user for confirmation
- Over-plan when scope is clear

### 3. Execution Phase

**DO**:

- Execute changes directly using appropriate tools
- Use `replace_string_in_file` with 3-5 lines of context before/after
- Run validation (tests, linting, type checking) after changes
- Continue iterating until rubric categories are satisfied

**DON'T**:

- Print code blocks instead of editing files
- Print terminal commands instead of running them
- Stop when encountering uncertainty

### 4. Validation & Iteration Phase

**DO**:

- Run tests if available (`runTests` tool)
- Check for errors (`get_errors` tool)
- Verify changes meet all rubric categories
- Iterate if any category falls short

**DON'T**:

- Skip validation
- Settle for "good enough"
- Hand back to user before completion

## Common Task Patterns

### Adding New Feature

1. **Context**: Search for similar existing features (`semantic_search`)
2. **Plan**: Identify UI layer, business logic, settings, i18n keys needed
3. **Execute**:
   - Add i18n keys to both `locales/*.json` files
   - Implement business logic in `utils/` or new module
   - Add UI widget in `modules/`
   - Update settings schema if needed
4. **Validate**: Run app, test feature, check for errors

### Fixing Bug

1. **Context**: Search for error message or symptom (`grep_search` for error text)
2. **Trace**: Read affected function and its callers (`list_code_usages`)
3. **Execute**: Apply fix with proper context
4. **Validate**: Run tests or reproduce scenario to confirm fix

### Refactoring

1. **Context**: Read target file completely
2. **Plan**: Identify code smells, duplication, complexity
3. **Execute**:
   - Extract functions/classes
   - Apply DRY principle
   - Maintain public API compatibility
4. **Validate**: Run tests, check for errors

## Critical Constraints

- **No inline diff display** - This tool orchestrates comparisons but shows results as symbols/percentages only. Actual side-by-side diff viewing delegated to external tools (VSCode, WinMerge, etc.)
- **PySide6 dependency** - Qt signals/slots pattern used throughout; hand-coded UI (no Qt Designer)
- **Multi-platform paths** - Use `pathlib.Path` consistently; avoid Windows-specific path operations

## Reference

For detailed project architecture and common tasks, see [.github/copilot-instructions.md](.github/copilot-instructions.md).

For project description and setup, see [README.md](README.md).
