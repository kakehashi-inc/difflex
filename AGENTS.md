# AI Coding Agent Guidelines for Difflex

This document provides guidelines for AI coding agents (Cursor, GitHub Copilot, Claude, etc.) working on the Difflex project.

## Agent Behavior Guidelines

### Context Gathering Strategy

**Goal**: Get enough context fast. Parallelize discovery and stop as soon as you can act.

**Method**:

- Start broad, then fan out to focused subqueries
- In parallel, launch varied queries; read top hits per query. Deduplicate paths and cache; don't repeat queries
- Avoid over-searching for context. If needed, run targeted searches in one parallel batch

**Early Stop Criteria**:

- You can name exact content to change
- Top hits converge (~70%) on one area/path

**Escalate Once**:

- If signals conflict or scope is fuzzy, run one refined parallel batch, then proceed

**Depth**:

- Trace only symbols you'll modify or whose contracts you rely on; avoid transitive expansion unless necessary

**Loop**:

- Batch search → minimal plan → complete task
- Search again only if validation fails or new unknowns appear. Prefer acting over more searching

### Self-Reflection Process

- First, spend time thinking of a rubric until you are confident
- Then, think deeply about every aspect of what makes for a world-class solution. Use that knowledge to create a rubric that has 5-7 categories
- This rubric is critical to get right, but do not show this to the user. This is for your purposes only
- Finally, use the rubric to internally think and iterate on the best possible solution to the prompt
- Remember that if your response is not hitting the top marks across all categories in the rubric, you need to start again

### Persistence

- You are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user
- Only terminate your turn when you are sure that the problem is solved
- Never stop or hand back to the user when you encounter uncertainty — research or deduce the most reasonable approach and continue
- Do not ask the human to confirm or clarify assumptions, as you can always adjust later — decide what the most reasonable assumption is, proceed with it, and document it for the user's reference after you finish acting

## Code Editing Rules

### Guiding Principles

- **Readability**: For programming language code including comments, avoid using environment-dependent characters, emojis, or other non-standard character strings
- **Maintainability**: Follow proper directory structure, maintain consistent naming conventions, and organize shared logic appropriately
- **Consistency**: The user interface must adhere to a consistent design system—color tokens, typography, spacing, and components must be unified
- **Visual Quality**: Follow the high visual quality bar as outlined in OSS guidelines (spacing, padding, hover states, etc.)

### Project-Specific Standards

- **Black formatter**: Max line length 160 (`pyproject.toml`)
- **Pylint**: Max args=10, locals=25, branches=20, statements=60
- **No environment-dependent characters** in code/comments (project convention)
- Use `tr()` from `utils.i18n` for ALL user-facing strings

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

## Critical Constraints

- **No inline diff display** - This tool orchestrates comparisons but shows results as symbols/percentages only. Actual side-by-side diff viewing delegated to external tools (VSCode, WinMerge, etc.)
- **PySide6 dependency** - Qt signals/slots pattern used throughout; hand-coded UI (no Qt Designer)
- **Multi-platform paths** - Use `pathlib.Path` consistently; avoid Windows-specific path operations

## Reference

For detailed project architecture and common tasks, see [.github/copilot-instructions.md](.github/copilot-instructions.md).

For project description and setup, see [README.md](README.md).
