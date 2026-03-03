"""
combiner.py — Pure logic for reading, validating, and merging CSV files.
Output is written as an Excel workbook (.xlsx) with a File Index sheet.
No GUI imports; safe to import from tests or other scripts.
"""

from pathlib import Path
import pandas as pd

_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1"]


def _read_csv(path: str, **kwargs) -> pd.DataFrame:
    """Try common encodings in order; raise the last error if all fail."""
    last_exc: Exception = RuntimeError("No encodings tried")
    for enc in _ENCODINGS:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError as exc:
            last_exc = exc
    raise last_exc


def validate_headers(file_paths: list[str]) -> tuple[bool, dict[str, str]]:
    """
    Validate that all files share the same column headers as the first file.

    Returns:
        (True, {})  — all headers match
        (False, {"input": "..."})  — fewer than 2 files provided
        (False, {"file1.csv": "...", ...})  — per-file mismatch details
    """
    if len(file_paths) < 2:
        return False, {"input": "At least 2 files are required for validation."}

    errors: dict[str, str] = {}

    # Read reference headers from the first file
    try:
        ref_df = _read_csv(file_paths[0], nrows=0)
        ref_cols = [str(c).strip() for c in ref_df.columns.tolist()]
    except Exception as exc:
        ref_name = Path(file_paths[0]).name
        return False, {ref_name: f"Could not read reference file: {exc}"}

    ref_set = set(ref_cols)

    for path in file_paths[1:]:
        name = Path(path).name
        try:
            df = _read_csv(path, nrows=0)
            cols = [str(c).strip() for c in df.columns.tolist()]
        except Exception as exc:
            errors[name] = f"Could not read file: {exc}"
            continue

        col_set = set(cols)
        issues: list[str] = []

        missing = ref_set - col_set
        if missing:
            issues.append(f"Missing columns: {sorted(missing)}")

        extra = col_set - ref_set
        if extra:
            issues.append(f"Extra columns: {sorted(extra)}")

        if not missing and not extra and cols != ref_cols:
            issues.append(
                f"Column order differs from reference. "
                f"Expected: {ref_cols}, got: {cols}"
            )

        if issues:
            errors[name] = "; ".join(issues)

    if errors:
        return False, errors
    return True, {}


def group_files_by_headers(
    file_paths: list[str],
) -> tuple[list[list[str]], dict[str, str]]:
    """
    Group files by their column set (order-independent).
    Files with the same set of column names land in the same group.

    Returns:
        (groups, errors)
        - groups: list of file-path lists; each inner list shares the same columns
        - errors: dict of filename -> error message for unreadable files
    """
    groups: list[list[str]] = []
    group_keys: list[frozenset] = []
    errors: dict[str, str] = {}

    for path in file_paths:
        name = Path(path).name
        try:
            df = _read_csv(path, nrows=0)
            key = frozenset(str(c).strip() for c in df.columns)
        except Exception as exc:
            errors[name] = f"Could not read file: {exc}"
            continue

        placed = False
        for i, existing_key in enumerate(group_keys):
            if existing_key == key:
                groups[i].append(path)
                placed = True
                break
        if not placed:
            groups.append([path])
            group_keys.append(key)

    return groups, errors


def _combine_group(file_paths: list[str], output_path: Path) -> tuple[bool, str]:
    """Concatenate a single group of CSV files (assumed same columns) into one xlsx."""
    frames: list[pd.DataFrame] = []
    index_rows: list[dict] = []
    warnings: list[str] = []

    for path in file_paths:
        name = Path(path).name
        try:
            df = _read_csv(path)
        except Exception as exc:
            return False, f"Failed to read '{name}': {exc}"

        row_count = len(df)
        if row_count == 0:
            warnings.append(f"'{name}' is header-only (0 data rows); included with 0 rows.")

        frames.append(df)
        index_rows.append(
            {
                "File Name": name,
                "Rows Combined": row_count,
                "Full Path": str(Path(path).resolve()),
            }
        )

    combined = pd.concat(frames, ignore_index=True)
    file_index = pd.DataFrame(index_rows, columns=["File Name", "Rows Combined", "Full Path"])

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            combined.to_excel(writer, sheet_name="Combined Data", index=False)
            file_index.to_excel(writer, sheet_name="File Index", index=False)
    except PermissionError:
        return (
            False,
            f"Permission denied writing to '{output_path.name}'. "
            "The file may be open in Excel — please close it and try again.",
        )
    except Exception as exc:
        return False, f"Failed to write '{output_path.name}': {exc}"

    msg_parts = [f"{len(combined)} rows from {len(file_paths)} file(s) → {output_path.resolve()}"]
    if warnings:
        msg_parts.extend(f"  Warning: {w}" for w in warnings)
    return True, "\n".join(msg_parts)


def combine_csv_files(
    file_paths: list[str], output_path: str
) -> tuple[bool, str]:
    """
    Group files by column format, then combine each group into its own xlsx.

    - Single group  → writes to output_path directly
    - Multiple groups → writes to output_stem_group_1.xlsx, _group_2.xlsx, …

    Output workbooks each have two sheets:
      "Combined Data" and "File Index" (File Name, Rows Combined, Full Path).

    Returns:
        (True, "Success message")
        (False, "Error message")
    """
    if len(file_paths) < 2:
        return False, "At least 2 files are required."

    groups, read_errors = group_files_by_headers(file_paths)

    if read_errors:
        lines = ["Could not read some files:"]
        lines.extend(f"  {name}: {msg}" for name, msg in read_errors.items())
        return False, "\n".join(lines)

    if not groups:
        return False, "No readable files found."

    out = Path(output_path)

    # Determine output paths per group
    if len(groups) == 1:
        output_paths = [out]
    else:
        output_paths = [
            out.parent / f"{out.stem}_group_{i + 1}{out.suffix}"
            for i in range(len(groups))
        ]

    result_lines = [
        f"Found {len(groups)} format group(s) across {len(file_paths)} files:",
    ]

    for i, (group, group_out) in enumerate(zip(groups, output_paths), 1):
        ok, msg = _combine_group(group, group_out)
        if not ok:
            return False, msg
        result_lines.append(f"  Group {i}: {msg}")

    return True, "\n".join(result_lines)
