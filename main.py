"""
main.py — tkinter GUI for CSV Combiner.
Calls combiner.py for all business logic; runs combine in a background thread.
Supports drag-and-drop of .csv files via tkinterdnd2.
"""

import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, scrolledtext

from tkinterdnd2 import DND_FILES, TkinterDnD

import combiner


class ExcelCombinerApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("CSV Combiner")
        self.resizable(True, True)
        self.minsize(600, 500)

        self.file_paths: list[str] = []
        self._output_modified_by_user = False

        self._build_ui()

    # ------------------------------------------------------------------ #
    #  UI Construction                                                     #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        padding = {"padx": 10, "pady": 5}

        # ── Section 1: File List ──────────────────────────────────────── #
        file_frame = tk.LabelFrame(self, text="CSV Files to Combine (or drag & drop here)")
        file_frame.pack(fill=tk.BOTH, expand=True, **padding)

        list_frame = tk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            height=8,
        )
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Register the listbox as a drag-and-drop target
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind("<<Drop>>", self._on_drop)

        btn_frame = tk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        tk.Button(btn_frame, text="Add Files", command=self._add_files).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(btn_frame, text="Remove Selected", command=self._remove_selected).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(btn_frame, text="Clear All", command=self._clear_all).pack(side=tk.LEFT)

        # ── Section 2: Output Path ────────────────────────────────────── #
        out_frame = tk.LabelFrame(self, text="Output File")
        out_frame.pack(fill=tk.X, **padding)

        self.output_var = tk.StringVar()
        self.output_var.trace_add("write", self._on_output_var_changed)
        self._output_var_internal_set = False

        inner = tk.Frame(out_frame)
        inner.pack(fill=tk.X, padx=5, pady=5)
        self.output_entry = tk.Entry(inner, textvariable=self.output_var)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        tk.Button(inner, text="Browse…", command=self._browse_output).pack(side=tk.LEFT)

        # ── Section 3: Action Buttons ─────────────────────────────────── #
        action_frame = tk.Frame(self)
        action_frame.pack(fill=tk.X, **padding)

        self.btn_validate = tk.Button(
            action_frame, text="Validate Headers", command=self._validate
        )
        self.btn_validate.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_combine = tk.Button(
            action_frame, text="Combine Files", command=self._combine
        )
        self.btn_combine.pack(side=tk.LEFT)

        # ── Section 4: Status / Log ───────────────────────────────────── #
        log_frame = tk.LabelFrame(self, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True, **padding)

        self.log = scrolledtext.ScrolledText(log_frame, state=tk.DISABLED, height=10)
        self.log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log.tag_config("error", foreground="red")
        self.log.tag_config("success", foreground="dark green")

    # ------------------------------------------------------------------ #
    #  File List Handlers                                                  #
    # ------------------------------------------------------------------ #

    def _try_add_path(self, path: str) -> bool:
        """Add a single file path if it's a valid .csv not already in the list.
        Returns True if added."""
        if not path.lower().endswith(".csv"):
            self._log(f"Skipped '{Path(path).name}': only .csv files are supported.", tag="error")
            return False
        if path in self.file_paths:
            self._log(f"Warning: '{Path(path).name}' is already in the list — skipped.")
            return False
        self.file_paths.append(path)
        self.listbox.insert(tk.END, Path(path).name)
        return True

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select CSV Files",
            filetypes=[("CSV files", "*.csv")],
        )
        added = sum(self._try_add_path(p) for p in paths)
        if added:
            self._log(f"Added {added} file(s).")
            self._maybe_set_default_output()

    def _on_drop(self, event):
        # tk.splitlist handles paths with spaces wrapped in {}
        paths = self.tk.splitlist(event.data)
        added = sum(self._try_add_path(p) for p in paths)
        if added:
            self._log(f"Added {added} file(s) via drag & drop.")
            self._maybe_set_default_output()

    def _remove_selected(self):
        selected = list(self.listbox.curselection())
        if not selected:
            self._log("No files selected to remove.")
            return
        for idx in reversed(selected):
            self.listbox.delete(idx)
            del self.file_paths[idx]
        self._log(f"Removed {len(selected)} file(s).")

    def _clear_all(self):
        count = len(self.file_paths)
        self.file_paths.clear()
        self.listbox.delete(0, tk.END)
        if count:
            self._log(f"Cleared {count} file(s).")

    # ------------------------------------------------------------------ #
    #  Output Path Handlers                                                #
    # ------------------------------------------------------------------ #

    def _on_output_var_changed(self, *_):
        # Distinguish programmatic vs. user edits
        if not self._output_var_internal_set:
            self._output_modified_by_user = True

    def _maybe_set_default_output(self):
        """Auto-populate the output path only if the user hasn't changed it."""
        if self._output_modified_by_user:
            return
        if not self.file_paths:
            return
        default = str(Path(self.file_paths[0]).parent / "combined_output.xlsx")
        self._output_var_internal_set = True
        self.output_var.set(default)
        self._output_var_internal_set = False

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Save Combined File As",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
        )
        if path:
            self._output_var_internal_set = True
            self.output_var.set(path)
            self._output_var_internal_set = False
            self._output_modified_by_user = True

    # ------------------------------------------------------------------ #
    #  Action Handlers                                                     #
    # ------------------------------------------------------------------ #

    def _validate(self):
        if len(self.file_paths) < 2:
            self._log("Please add at least 2 files before validating.", tag="error")
            return

        self._log("Analyzing file formats…")
        groups, errors = combiner.group_files_by_headers(self.file_paths)

        if errors:
            for name, msg in errors.items():
                self._log(f"  Could not read '{name}': {msg}", tag="error")

        if not groups:
            return

        if len(groups) == 1:
            self._log(
                f"All {len(self.file_paths)} files share the same format — will produce 1 output file.",
                tag="success",
            )
        else:
            self._log(
                f"Found {len(groups)} distinct format(s) — will produce {len(groups)} output files:",
                tag="success",
            )
            for i, group in enumerate(groups, 1):
                names = ", ".join(Path(p).name for p in group)
                self._log(f"  Group {i} ({len(group)} file(s)): {names}")

    def _combine(self):
        if len(self.file_paths) < 2:
            self._log("Please add at least 2 files before combining.", tag="error")
            return

        output_path = self.output_var.get().strip()
        if not output_path:
            self._log("Please specify an output file path.", tag="error")
            return

        self._set_buttons_enabled(False)
        self._log("Combining files…")

        def _worker():
            ok, msg = combiner.combine_csv_files(self.file_paths, output_path)
            self.after(0, lambda: self._on_combine_done(ok, msg))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _on_combine_done(self, ok: bool, msg: str):
        tag = "success" if ok else "error"
        self._log(msg, tag=tag)
        self._set_buttons_enabled(True)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _set_buttons_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.btn_validate.config(state=state)
        self.btn_combine.config(state=state)

    def _log(self, message: str, tag: str | None = None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        self.log.config(state=tk.NORMAL)
        if tag:
            self.log.insert(tk.END, line, tag)
        else:
            self.log.insert(tk.END, line)
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)


if __name__ == "__main__":
    app = ExcelCombinerApp()
    app.mainloop()
