# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

CSV Combiner — a desktop GUI tool for merging multiple CSV files into a single Excel workbook. Files with matching column headers are combined into one output; files with different column formats are automatically grouped into separate output files. Each output contains a "Combined Data" sheet and a "File Index" sheet showing source file provenance.

## Git Commit & Push Policy

**Commit and push after every code change** to keep GitHub in sync. Specifically:
- Commit after every meaningful change (new file, new feature, bug fix, refactor)
- Commit before and after any significant structural change
- Never leave a session with uncommitted or unpushed changes
- Use descriptive commit messages that explain *what* and *why*
- Always run `git push` immediately after committing
- Always run `git status` at the end of a session to confirm everything is committed and pushed

## Setup & Usage

Install dependencies (requires Python 3.10+):
```
pip install -r requirements.txt
```

Run the GUI:
```
python main.py
```

## File Structure

```
Excel-Combiner/
├── main.py                        # tkinter GUI
├── combiner.py                    # Pure logic (no GUI imports)
├── requirements.txt               # Python dependencies
├── README.md                      # Public-facing documentation
├── LICENSE                        # MIT License
├── .gitignore                     # Python, macOS, PyInstaller ignores
└── .github/
    └── workflows/
        └── build.yml              # GitHub Actions: build & release
```

## Architecture

| File | Role |
|------|------|
| `combiner.py` | Pure logic — no GUI imports. Public functions: `validate_headers`, `group_files_by_headers`, `combine_csv_files`. Private helpers: `_read_csv`, `_combine_group`. Safe to import from tests or scripts. |
| `main.py` | tkinter GUI (`ExcelCombinerApp`). Inherits from `TkinterDnD.Tk` for drag-and-drop support. All business logic delegated to `combiner.py`. Combine runs in a daemon thread; results posted back via `self.after(0, callback)`. |
| `requirements.txt` | `pandas>=2.0.0`, `openpyxl>=3.1.0`, `tkinterdnd2>=0.3.0` |
| `.github/workflows/build.yml` | Triggers on version tags (`v*`). Builds macOS `.app` and Windows `.exe` via PyInstaller on GitHub-hosted runners, then publishes both as assets on a GitHub Release. |

## Key Decisions

- **Input format**: `.csv` only — non-CSV files are rejected at the GUI level with a clear message
- **Encoding**: auto-detects `utf-8` → `utf-8-sig` → `latin-1` via `_read_csv()` helper
- **Grouping**: files are grouped by their column set (`frozenset`) — order-independent; `pd.concat` aligns columns by name automatically
- **Single group**: writes to the specified output path directly
- **Multiple groups**: writes to `combined_output_group_1.xlsx`, `combined_output_group_2.xlsx`, etc.
- **Output sheets**: `"Combined Data"` (concatenated rows) + `"File Index"` (File Name, Rows Combined, Full Path)
- **Empty files**: included with 0 rows; warning logged but combine continues
- **Output dir**: auto-created with `mkdir(parents=True, exist_ok=True)`
- **Default output path**: auto-set to first file's directory as `combined_output.xlsx`; not overridden if user has manually edited the field
- **Drag & drop**: uses `tkinterdnd2`; `tk.splitlist(event.data)` handles macOS paths with spaces
- **Threading**: combine runs in a `daemon=True` thread; buttons disabled during operation
- **Output engine**: `openpyxl` for writing `.xlsx`

## Releasing a New Version

1. Tag the commit and push:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. GitHub Actions builds macOS and Windows binaries automatically (~5 min)
3. Check build status at: `https://github.com/stargate-code/Excel-Combiner/actions`
4. Edit the auto-created release at: `https://github.com/stargate-code/Excel-Combiner/releases`
5. Add release notes and publish

## GitHub Repository

- **URL**: `https://github.com/stargate-code/Excel-Combiner`
- **Visibility**: Public
- **License**: MIT
- **Latest release**: `https://github.com/stargate-code/Excel-Combiner/releases/latest`
