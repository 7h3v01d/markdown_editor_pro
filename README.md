# Markdown Editor Pro

A dark-industrial markdown editor and viewer for the desktop. Single-file, PyQt6, two dependencies, zero ceremony.

Split-pane editing with live preview, markdown syntax highlighting, a line-numbered gutter, synchronized scrolling, document structure navigation, and print/PDF output — wrapped in a navy/teal/amber industrial theme (with phosphor-terminal and light alternatives).

## Features

- **Live preview** — debounced re-render as you type (450 ms), with scroll position preserved
- **Markdown syntax highlighting** — headings, bold/italic, inline and fenced code, links, blockquotes, list markers, horizontal rules
- **Line-number gutter** — with current-line indicator and current-line background highlight
- **Sync scroll** — proportional two-way scroll linking between editor and preview, toggleable from the toolbar
- **Document structure panel** — click any heading to jump to it (editor line in editor mode, rendered section in viewer mode)
- **Print / PDF** — prints the rendered preview via the system print dialog; always uses light styling so dark themes don't print solid page backgrounds. Use "Microsoft Print to PDF" for free PDF export
- **Three themes** — `obsidian` (navy/teal/amber, default), `phosphor` (green terminal), `daylight` (light)
- **Editor and viewer modes** — viewer mode is read-only with markdown rendered in safe mode
- **Live stats** — cursor line:column, word count, and character count in the status bar
- **Unsaved-changes guard** — on open, reload, and close
- **Self-installing dependencies** — prompts to `pip install` anything missing on first run

## Requirements

- Python 3.10+
- [PyQt6](https://pypi.org/project/PyQt6/)
- [markdown2](https://pypi.org/project/markdown2/)

```
pip install -r requirements.txt
```

Or just run it — the script detects missing dependencies and offers to install them.

## Usage

```
python Markdown_Editor_Pro.py [file] [options]
```

| Option | Description |
|---|---|
| `file` | Optional markdown file to open on startup |
| `--mode {editor,viewer}` | Override the built-in mode (default: `editor`) |
| `--theme {obsidian,phosphor,daylight}` | Override the default theme |
| `--no-install` | Exit instead of prompting to install missing dependencies |

Examples:

```
python Markdown_Editor_Pro.py README.md
python Markdown_Editor_Pro.py notes.md --theme phosphor
python Markdown_Editor_Pro.py docs/spec.md --mode viewer
```

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Open file |
| `Ctrl+S` | Save |
| `Ctrl+Shift+S` | Save As |
| `Ctrl+R` | Reload file from disk |
| `Ctrl+P` | Print preview pane |
| `F5` | Refresh preview |
| `Ctrl+=` / `Ctrl+-` | Editor font size up / down |

## Configuration

Defaults live at the top of the script:

```python
APP_MODE = "editor"            # "editor" | "viewer"
DEFAULT_THEME = "obsidian"     # "obsidian" | "phosphor" | "daylight"
LIVE_PREVIEW_DELAY_MS = 450
```

Themes are plain colour dictionaries in the `THEMES` mapping — add your own by copying an existing entry; it will appear in the theme selector automatically.

## Notes

- The preview uses `QTextBrowser`, which renders the standard markdown output (tables, fenced code, blockquotes, images) with a small footprint. For pixel-perfect HTML/CSS rendering, the pipeline is isolated enough that swapping in `PyQt6-WebEngine` is a small change.
- Relative image paths in documents resolve against the file's directory in both the preview and printed output.
- Fonts fall back gracefully: JetBrains Mono → Cascadia Code → Consolas.

## License

Apache License 2.0 — Copyright (c) 2026 Leon Priest ([7h3v01d](https://github.com/7h3v01d))
