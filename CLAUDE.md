# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Excel Combiner — a desktop GUI tool for merging multiple Excel files (with matching column headers) into a single output workbook. The output contains a "Combined Data" sheet and a "File Index" sheet showing source file provenance.

## Git Commit Policy

**Commit frequently throughout every session** to ensure no work is lost. Specifically:
- Commit after every meaningful change (new file, new feature, bug fix, refactor)
- Commit before and after any significant structural change
- Never leave a session with uncommitted changes
- Use descriptive commit messages that explain *what* and *why*
- Always run `git status` at the end of a session to confirm everything is committed

## Setup & Usage

Install dependencies (requires Python 3.10+):
```
pip install -r requirements.txt
```

Run the GUI:
```
python main.py
```

## Architecture

| File | Role |
|------|------|
| `combiner.py` | Pure logic — no GUI imports. Two public functions: `validate_headers` and `combine_excel_files`. Safe to import from tests or scripts. |
| `main.py` | tkinter GUI (`ExcelCombinerApp`). All business logic delegated to `combiner.py`. Combine operation runs in a daemon thread; results posted back to the main thread via `self.after(0, callback)`. |
| `requirements.txt` | `pandas>=2.0.0`, `openpyxl>=3.1.0` |

### Key decisions
- **Engine**: `openpyxl` only — `.xls` files are rejected with a clear message.
- **Sheet selection**: first sheet by index (`sheet_name=0`), not by name.
- **Header comparison**: whitespace-stripped; reports missing, extra, and order-mismatch separately.
- **Output sheets**: `"Combined Data"` (concatenated rows) + `"File Index"` (File Name, Rows Combined, Full Path).
- **Empty files**: included with 0 rows; warning logged but combine continues.
- **Output dir**: auto-created with `mkdir(parents=True, exist_ok=True)`.
- **Default output path**: auto-set to first file's directory as `combined_output.xlsx`; cleared if user manually edits the field.
