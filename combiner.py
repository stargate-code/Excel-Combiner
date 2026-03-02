"""
combiner.py — Pure logic for reading, validating, and merging Excel files.
No GUI imports; safe to import from tests or other scripts.
"""

from pathlib import Path
import pandas as pd


def validate_headers(file_paths: list[str]) -> tuple[bool, dict[str, str]]:
    """
    Validate that all files share the same column headers as the first file.

    Returns:
        (True, {})  — all headers match
        (False, {"input": "..."})  — fewer than 2 files provided
        (False, {"file1.xlsx": "...", ...})  — per-file mismatch details
    """
    if len(file_paths) < 2:
        return False, {"input": "At least 2 files are required for validation."}

    errors: dict[str, str] = {}

    # Read reference headers from the first file
    try:
        ref_df = pd.read_excel(file_paths[0], nrows=0, engine="openpyxl")
        ref_cols = [str(c).strip() for c in ref_df.columns.tolist()]
    except Exception as exc:
        ref_name = Path(file_paths[0]).name
        return False, {ref_name: f"Could not read reference file: {exc}"}

    ref_set = set(ref_cols)

    for path in file_paths[1:]:
        name = Path(path).name
        try:
            df = pd.read_excel(path, nrows=0, engine="openpyxl")
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


def combine_excel_files(
    file_paths: list[str], output_path: str
) -> tuple[bool, str]:
    """
    Validate headers, concatenate all first sheets, and write output.

    Output workbook has two sheets:
      - "Combined Data": all rows concatenated
      - "File Index": File Name, Rows Combined, Full Path

    Returns:
        (True, "Success message")
        (False, "Error message")
    """
    # --- Validate headers first ---
    valid, header_errors = validate_headers(file_paths)
    if not valid:
        lines = ["Header validation failed:"]
        for key, msg in header_errors.items():
            lines.append(f"  {key}: {msg}")
        return False, "\n".join(lines)

    frames: list[pd.DataFrame] = []
    index_rows: list[dict] = []
    warnings: list[str] = []

    # --- Read each file ---
    for path in file_paths:
        name = Path(path).name
        try:
            df = pd.read_excel(path, sheet_name=0, engine="openpyxl")
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

    # --- Concatenate ---
    combined = pd.concat(frames, ignore_index=True)
    file_index = pd.DataFrame(index_rows, columns=["File Name", "Rows Combined", "Full Path"])

    # --- Ensure output directory exists ---
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # --- Write output workbook ---
    try:
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            combined.to_excel(writer, sheet_name="Combined Data", index=False)
            file_index.to_excel(writer, sheet_name="File Index", index=False)
    except PermissionError:
        return (
            False,
            f"Permission denied writing to '{out.name}'. "
            "The file may be open in Excel — please close it and try again.",
        )
    except Exception as exc:
        return False, f"Failed to write output file: {exc}"

    total_rows = len(combined)
    msg_parts = [
        f"Success! Combined {total_rows} rows from {len(file_paths)} files.",
        f"Output saved to: {out.resolve()}",
    ]
    if warnings:
        msg_parts.append("Warnings:")
        msg_parts.extend(f"  {w}" for w in warnings)

    return True, "\n".join(msg_parts)
