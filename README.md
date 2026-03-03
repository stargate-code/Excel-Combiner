# CSV Combiner

A simple desktop app for merging multiple CSV files into a single Excel workbook.

## Features

- **Combine CSV files** — merges multiple CSVs into one `.xlsx` output
- **Auto-grouping** — if files have different column formats, they are automatically grouped and saved into separate output files
- **Header validation** — preview how files will be grouped before combining
- **File Index sheet** — tracks the source file name, row count, and full path for every file combined
- **Drag & drop** — drag CSV files directly into the app (macOS)
- **Encoding support** — handles UTF-8, UTF-8 BOM, and Latin-1 encoded files automatically

## Download

Go to the [Releases](https://github.com/stargate-code/Excel-Combiner/releases/latest) page and download the file for your OS:

| Platform | File |
|----------|------|
| macOS | `CSV-Combiner-macOS.zip` — extract and open `CSV Combiner.app` |
| Windows | `CSV Combiner.exe` — run directly, no install needed |

> **macOS note:** You may see an "unidentified developer" warning. Right-click the app and select **Open** to bypass it.

## How to Use

1. Open the app
2. Click **Add Files** or drag & drop CSV files into the file list
3. Set the output file path (auto-filled by default)
4. Click **Validate Headers** to preview how files will be grouped *(optional)*
5. Click **Combine Files**
6. Find your output `.xlsx` file(s) at the specified path

## Output

Each output workbook contains two sheets:

- **Combined Data** — all rows from the combined CSV files
- **File Index** — source file name, row count, and full path for each input file

## Run from Source

Requires Python 3.10+

```bash
git clone https://github.com/stargate-code/Excel-Combiner.git
cd Excel-Combiner
pip install -r requirements.txt
python main.py
```

## License

[MIT](LICENSE)
