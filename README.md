# Markdown Editor Pro & Markdown Viewer Pro

A matched pair of dark-industrial markdown tools for the desktop. Single-file PyQt6 apps, two dependencies, zero ceremony.

- **Markdown_Editor_Pro.py** — split-pane editor with live preview, syntax highlighting, and synchronized scrolling
- **Markdown_Viewer_Pro.py** — read-only reader with search, zoom, auto-refresh, and recent files

Both share the same design language: a navy/teal/amber industrial theme (with phosphor-terminal and light alternatives), JetBrains Mono accents, and identical toolbar, panel, and status-bar layouts.

## Markdown Editor Pro

<img width="1920" height="1040" alt="markdown_editor_pro" src="https://github.com/user-attachments/assets/30430b1a-4a31-4b97-9aa7-9d3a7bca7277" /><br>

- **Live preview** — debounced re-render as you type (450 ms), with scroll position preserved
- **Markdown syntax highlighting** — headings, bold/italic, inline and fenced code, links, blockquotes, list markers, horizontal rules
- **Line-number gutter** — with current-line indicator and current-line background highlight
- **Sync scroll** — proportional two-way scroll linking between editor and preview, toggleable from the toolbar
- **Document structure panel** — click any heading to jump to that line
- **Print / PDF** — prints the rendered preview via the system print dialog
- **Editor and viewer modes** — `--mode viewer` gives a read-only window with markdown rendered in safe mode
- **Live stats** — cursor line:column, word count, and character count
- **Unsaved-changes guard** — on open, reload, and close

```
python Markdown_Editor_Pro.py [file] [--mode editor|viewer] [--theme obsidian|phosphor|daylight]
```

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Open file |
| `Ctrl+S` / `Ctrl+Shift+S` | Save / Save As |
| `Ctrl+R` | Reload file from disk |
| `Ctrl+P` | Print preview pane |
| `F5` | Refresh preview |
| `Ctrl+=` / `Ctrl+-` | Editor font size up / down |

## Markdown Viewer Pro

- **Reader-focused** — no editing surface, just the rendered document with a structure panel
- **Find** — live match count with highlighting; `Enter` cycles matches
- **Zoom** — 60–180% document scaling from the toolbar or keyboard
- **Auto-refresh** — watches the open file and re-renders when it changes on disk (2 s poll), with a status-bar flash
- **Recent files** — last 10 files persisted to `~/.mdviewer_recent.json`, available from the `RECENT` dropdown
- **Drag & drop** — drop a markdown file anywhere in the window to open it
- **Print / PDF** — same clean light-styled print pipeline as the editor
- **Extended markdown** — footnotes, strikethrough, task lists (rendered as ☑/☐), and smart typography
- **Fullscreen reading** — `F11`

```
python Markdown_Viewer_Pro.py [file] [--theme obsidian|phosphor|daylight]
```

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Open file |
| `Ctrl+F` / `Esc` | Find / close find |
| `Ctrl+T` | Cycle theme |
| `Ctrl+P` | Print |
| `Ctrl+R` / `F5` | Refresh |
| `Ctrl+=` / `Ctrl+-` / `Ctrl+0` | Zoom in / out / reset |
| `F11` | Fullscreen |
| `Ctrl+Q` | Quit |

## Requirements

- Python 3.10+
- [PyQt6](https://pypi.org/project/PyQt6/)
- [markdown2](https://pypi.org/project/markdown2/)

```
pip install -r requirements.txt
```

Or just run either script — both detect missing dependencies and offer to install them. Add `--no-install` to exit instead of prompting.

## Themes

Three themes, shared by both apps and selectable from the toolbar or `--theme`:

| Theme | Character |
|---|---|
| `obsidian` (default) | Deep navy, teal accents, amber headings |
| `phosphor` | Green-on-black terminal |
| `daylight` | Light, for bright rooms |

Themes are plain colour dictionaries in the `THEMES` mapping at the top of each script — add your own by copying an existing entry; it will appear in the theme selector automatically.

## Printing

Both apps print the rendered document through the standard system print dialog (`Ctrl+P`). Output always uses the light stylesheet regardless of the active theme, so dark themes don't print solid page backgrounds. Choose "Microsoft Print to PDF" in the dialog for PDF export.

## Notes

- Rendering uses `QTextBrowser`, which handles the standard markdown output (tables, fenced code, blockquotes, images) with a small footprint. For pixel-perfect HTML/CSS rendering, the pipeline is isolated enough that swapping in `PyQt6-WebEngine` is a small change.
- Relative image paths resolve against the document's directory in both the preview and printed output.
- Fonts fall back gracefully: JetBrains Mono → Cascadia Code → Consolas.

## License

Apache License 2.0 — Copyright (c) 2026 Leon Priest ([7h3v01d](https://github.com/7h3v01d))
