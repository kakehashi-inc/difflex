# Difflex - AI Coding Agent Instructions

## Project Overview

Difflex is a cross-platform (Windows/macOS/Linux) GUI file and directory comparison tool built with **PySide6**. It delegates actual diff visualization to external tools while handling comparison logic, similarity detection, and workflow orchestration internally.

## Architecture

### Core Components

- **Entry Point**: `src/difflex/main.py` - Initializes Qt app, i18n system, and main window
- **UI Layer**: `src/difflex/modules/` - Tab-based UI with home screen, comparison widgets, and settings
  - `main_window.py` - QMainWindow with tab management and menu bar
  - `home_widget.py` - Landing page for initiating comparisons via drag-drop or file selection
  - `file_comparison_widget.py`, `parallel_comparison_widget.py` - Comparison result displays
  - `comparison_worker.py` - QThread for background directory comparison
- **Comparison Engine**: `src/difflex/utils/comparator.py` - Three comparator classes:
  - `TextComparator` - Normalizes line endings/whitespace, uses difflib
  - `ImageComparator` - Pixel-level comparison with PIL/numpy, detects EXIF-only differences
  - `BinaryComparator` - Byte-level comparison with similarity percentage
- **Settings & i18n**:
  - `utils/settings.py` - QSettings-based persistence for thresholds, file extensions, external tools
  - `utils/i18n.py` - JSON-based translation system (`locales/ja-JP.json`, `locales/en-US.json`)

### Comparison Result Symbols
- `=` Identical
- `≒` Similar (within threshold)
- `≒EX` Similar except EXIF metadata
- `≠` Different

### Data Flow
1. User selects 2-3 files/directories in home screen
2. Comparison request stored in history (`utils/settings.py`)
3. New tab created with `ComparisonWidget`
4. For directories: `DirectoryComparisonWorker` (QThread) recursively scans, emits progress signals
5. Results displayed with position-aligned comparison status indicators
6. Double-click file → launch external diff tool with configured arguments

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

### Code Standards
- **Black formatter**: Max line length 160 (`pyproject.toml`)
- **Pylint**: Max args=10, locals=25, branches=20, statements=60
- **No environment-dependent characters** in code/comments (project convention)
- Use `tr()` from `utils.i18n` for ALL user-facing strings

### Translation Workflow
1. Add keys to `locales/en-US.json` and `locales/ja-JP.json`
2. Use `tr("key_name")` in UI code
3. Auto-detects system locale on first run; user can override in settings

## Project-Specific Patterns

### External Tool Integration
Settings store per-file-type (text/image/binary) tool configurations:
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
When launching tools, unused `%s` placeholders are either removed (pack_args=True) or kept as gaps.

### Multi-Encoding Text Handling
`TextComparator.compare()` attempts UTF-8, UTF-8-sig, Shift-JIS, CP932, Latin-1 in sequence to handle diverse source files (Japanese project).

### Background Comparison Architecture
`DirectoryComparisonWorker` emits three signal types:
- `progress(current, total, message)` - Update progress bar
- `file_found(FileComparisonItem)` - Add item to UI immediately
- `comparison_complete(item, results)` - Update item with comparison results

Workers can be stopped mid-execution via `worker.stop()` - app remains responsive during long comparisons.

### Theme System
Dark/light mode controlled by `Settings.get_dark_mode()`:
- Defaults to OS theme on first run
- Apply theme in `MainWindow._apply_theme()` using Qt stylesheets
- User can toggle in settings dialog

## Key Files Reference

- **Comparison logic**: `utils/comparator.py` (228 lines) - Study `ComparisonResult` class and three comparator implementations
- **Settings schema**: `utils/settings.py` (206 lines) - All persistent config keys and defaults
- **Worker pattern**: `modules/comparison_worker.py` - Template for background processing
- **External tool launching**: `modules/file_comparison_widget.py` - See `_launch_external_tool()` method
- **Requirements doc**: `Documents/ファイル比較アプリ要件定義.md` - Original Japanese spec (authoritative for feature disputes)

## Common Tasks

### Adding New File Type
1. Update `DEFAULT_*_EXTENSIONS` in `utils/settings.py`
2. Add detection logic in `utils/file_types.py`
3. Consider adding specialized comparator if needed

### Adding Translation Key
1. Add to both `locales/en-US.json` and `locales/ja-JP.json`
2. Use `tr("new_key")` in code
3. Restart app to test (no hot reload)

### Modifying Comparison Threshold
- Default thresholds: Text=95%, Image=99%, Binary=100%
- Stored per-user in QSettings
- Exposed in settings dialog as spin boxes (0-100)

## Build & Distribution

- **Windows**: `build_windows.ps1` → Nuitka single-file .exe
- **macOS**: `build_macos.zsh` → App bundle
- **Linux**: `build_linux.sh` → Binary
- **PyPI**: See `Documents/pypiリリース方法.md` for release process
- All builds use `assets/app.ico` or `app.png` for application icon

## Critical Constraints

- **No inline diff display** - This tool orchestrates comparisons but shows results as symbols/percentages only. Actual side-by-side diff viewing delegated to external tools (VSCode, WinMerge, etc.)
- **PySide6 dependency** - Qt signals/slots pattern used throughout; familiar with Qt Designer workflows not required (hand-coded UI)
- **Multi-platform paths** - Use `pathlib.Path` consistently; avoid Windows-specific path operations
