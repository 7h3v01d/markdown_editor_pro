#!/usr/bin/env python3
"""
Markdown Viewer Pro — PyQt6 Edition
====================================
A dark-industrial, read-only markdown viewer. Companion to Markdown Editor Pro.

    python Markdown_Viewer_Pro.py [file] [--theme obsidian|phosphor|daylight]

Copyright (c) 2026 Leon Priest (7h3v01d)
Licensed under the Apache License, Version 2.0
"""

import sys
import re
import json
import argparse
import importlib.util
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# ==============================================================================
# CONFIGURATION
# ==============================================================================

DEFAULT_THEME = "obsidian"     # "obsidian" | "phosphor" | "daylight"
WINDOW_TITLE = "Markdown Viewer Pro"
WATCHER_INTERVAL_MS = 2000     # auto-refresh mtime poll
RECENT_FILES_PATH = Path.home() / ".mdviewer_recent.json"
MAX_RECENT_FILES = 10
MONO_STACK = ["JetBrains Mono", "Cascadia Code", "Consolas", "Courier New"]
UI_STACK = ["Segoe UI", "Inter", "Arial"]

REQUIRED_DEPENDENCIES = {
    "markdown2": "markdown2>=2.4.0",
    "PyQt6": "PyQt6>=6.4.0",
}

MARKDOWN_EXTRAS = [
    "fenced-code-blocks", "tables", "header-ids", "footnotes",
    "strike", "task_list", "smartypants", "cuddled-lists",
]

THEMES: Dict[str, Dict[str, str]] = {
    "obsidian": {
        "bg":           "#0b1220",
        "panel":        "#101a2c",
        "panel2":       "#0e1626",
        "border":       "#1e2f4a",
        "fg":           "#d7e2f0",
        "muted":        "#6b7f9c",
        "accent":       "#2dd4bf",
        "accent2":      "#f5a524",
        "select_bg":    "#173a52",
        "select_fg":    "#e8f4ff",
        "editor_bg":    "#0a101c",
        "gutter_bg":    "#0d1424",
        "gutter_fg":    "#3d5474",
        "cursor_line":  "#0f1a30",
        "code_fg":      "#7ee7d8",
        "code_bg":      "#0e1a2e",
        "link":         "#4cc2ff",
        "quote_bg":     "#0e1727",
        "quote_border": "#2dd4bf",
        "danger":       "#ff5c5c",
    },
    "phosphor": {
        "bg":           "#050a06",
        "panel":        "#0a120b",
        "panel2":       "#081008",
        "border":       "#1c3a20",
        "fg":           "#8dff9c",
        "muted":        "#3f7a48",
        "accent":       "#39ff5e",
        "accent2":      "#c8ff39",
        "select_bg":    "#123a1a",
        "select_fg":    "#d8ffdc",
        "editor_bg":    "#040805",
        "gutter_bg":    "#070f08",
        "gutter_fg":    "#2c5c34",
        "cursor_line":  "#08140a",
        "code_fg":      "#c8ff39",
        "code_bg":      "#0a140b",
        "link":         "#5effc0",
        "quote_bg":     "#081408",
        "quote_border": "#39ff5e",
        "danger":       "#ff6a3d",
    },
    "daylight": {
        "bg":           "#f6f8fa",
        "panel":        "#ffffff",
        "panel2":       "#eef1f5",
        "border":       "#d0d7de",
        "fg":           "#111827",
        "muted":        "#6b7280",
        "accent":       "#0d9488",
        "accent2":      "#b45309",
        "select_bg":    "#cfe8ff",
        "select_fg":    "#111827",
        "editor_bg":    "#ffffff",
        "gutter_bg":    "#f0f3f7",
        "gutter_fg":    "#9aa5b1",
        "cursor_line":  "#f2f6fb",
        "code_fg":      "#0f766e",
        "code_bg":      "#eef1f5",
        "link":         "#0969da",
        "quote_bg":     "#f2f4f7",
        "quote_border": "#0d9488",
        "danger":       "#b91c1c",
    },
}

MARKDOWN_FILE_FILTER = (
    "Markdown files (*.md *.markdown *.mdown *.mkd);;"
    "Text files (*.txt);;All files (*.*)"
)


# ==============================================================================
# ARGUMENT PARSING / DEPENDENCY CHECK
# ==============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=WINDOW_TITLE)
    parser.add_argument("file", nargs="?", help="Optional markdown file to open on startup.")
    parser.add_argument("--theme", choices=list(THEMES.keys()), help="Override the default theme.")
    parser.add_argument("--no-install", action="store_true",
                        help="Exit instead of prompting to install missing dependencies.")
    return parser.parse_args()


def check_and_install_dependencies(args: argparse.Namespace) -> None:
    missing: List[str] = [
        spec for name, spec in REQUIRED_DEPENDENCIES.items()
        if importlib.util.find_spec(name) is None
    ]
    if not missing:
        return

    print(f"[!] Missing dependencies required to run {WINDOW_TITLE}.")
    in_venv = sys.prefix != sys.base_prefix
    cmd = [sys.executable, "-m", "pip", "install"]
    if not in_venv:
        cmd.append("--user")
    cmd.extend(missing)
    printable = " ".join(f'"{p}"' if " " in p else p for p in cmd)
    print(f"\n    {printable}\n")

    if args.no_install:
        print("Skipping installation because --no-install was provided.")
        sys.exit(1)

    if sys.stdin and sys.stdin.isatty():
        if input("Install missing packages now? (y/n): ").strip().lower() == "y":
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print("[!] Installation failed.")
                print(result.stdout)
                print(result.stderr)
                sys.exit(1)
            print("[+] Dependencies installed. Please re-run the program.")
            sys.exit(0)
    sys.exit(1)


ARGS = parse_args()
check_and_install_dependencies(ARGS)

# Third-party imports only after dependency check
import markdown2  # noqa: E402
from PyQt6.QtCore import Qt, QTimer, QUrl  # noqa: E402
from PyQt6.QtGui import (  # noqa: E402
    QFont, QColor, QKeySequence, QShortcut, QTextCharFormat,
    QTextCursor, QTextDocument,
)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog  # noqa: E402
from PyQt6.QtWidgets import (  # noqa: E402
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSplitter, QListWidget, QListWidgetItem,
    QTextEdit, QTextBrowser, QFrame, QFileDialog, QMessageBox, QSizePolicy,
    QLineEdit, QMenu, QDialog,
)


def make_font(families: List[str], size: int, bold: bool = False) -> QFont:
    font = QFont()
    font.setFamilies(families)
    font.setPointSize(size)
    font.setBold(bold)
    return font


# ==============================================================================
# MAIN WINDOW
# ==============================================================================

class MarkdownViewerPro(QMainWindow):
    def __init__(self, startup_file: Optional[str], theme_name: str) -> None:
        super().__init__()
        self.theme_name = theme_name if theme_name in THEMES else DEFAULT_THEME
        self.theme = THEMES[self.theme_name]

        self.file_path: Optional[str] = None
        self.md_content: str = ""
        self.file_mtime: float = 0.0
        self.headings: List[Dict[str, object]] = []
        self.zoom: float = 1.0
        self.recent_files: List[str] = self.load_recent()
        self.search_matches: List[QTextCursor] = []
        self.search_index: int = -1

        self.watcher = QTimer(self)
        self.watcher.setInterval(WATCHER_INTERVAL_MS)
        self.watcher.timeout.connect(self.check_file_changed)

        self.dot_timer = QTimer(self)
        self.dot_timer.setSingleShot(True)
        self.dot_timer.setInterval(3000)
        self.dot_timer.timeout.connect(lambda: self.refresh_dot.setVisible(False))

        self.setAcceptDrops(True)

        self.build_ui()
        self.bind_shortcuts()
        self.apply_theme()

        self.resize(1180, 760)
        self.setMinimumSize(820, 560)

        if startup_file and Path(startup_file).exists():
            self.load_file(startup_file)
        else:
            self.show_welcome()
        self.update_window_title()

    # --------------------------------------------------------------------------
    # UI construction
    # --------------------------------------------------------------------------

    def build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(central)

        # ---- Toolbar -----------------------------------------------------------
        self.toolbar = QFrame()
        self.toolbar.setObjectName("Toolbar")
        bar = QHBoxLayout(self.toolbar)
        bar.setContentsMargins(14, 8, 14, 8)
        bar.setSpacing(8)

        self.app_label = QLabel("MD//VIEW")
        self.app_label.setObjectName("AppMark")
        self.app_label.setFont(self._spaced_font(MONO_STACK, 12, bold=True, spacing=140))
        bar.addWidget(self.app_label)

        bar.addSpacing(10)

        self.open_button = self._tool_button("OPEN", self.choose_and_open_file)
        bar.addWidget(self.open_button)

        self.recent_button = self._tool_button("RECENT", self.show_recent_menu)
        bar.addWidget(self.recent_button)

        self.refresh_button = self._tool_button("REFRESH", self.refresh)
        bar.addWidget(self.refresh_button)

        self.find_button = self._tool_button("FIND", self.open_search)
        bar.addWidget(self.find_button)

        self.print_button = self._tool_button("PRINT", self.print_document)
        bar.addWidget(self.print_button)

        bar.addSpacing(12)

        # Zoom group
        self.zoom_out_button = self._tool_button("−", lambda: self.adjust_zoom(-0.1))
        self.zoom_out_button.setFixedWidth(30)
        bar.addWidget(self.zoom_out_button)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setObjectName("ZoomLabel")
        self.zoom_label.setFont(make_font(MONO_STACK, 8))
        self.zoom_label.setFixedWidth(42)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar.addWidget(self.zoom_label)

        self.zoom_in_button = self._tool_button("+", lambda: self.adjust_zoom(0.1))
        self.zoom_in_button.setFixedWidth(30)
        bar.addWidget(self.zoom_in_button)

        bar.addStretch(1)

        self.path_label = QLabel("NO FILE LOADED")
        self.path_label.setObjectName("PathLabel")
        self.path_label.setFont(make_font(MONO_STACK, 8))
        self.path_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        bar.addWidget(self.path_label)

        bar.addSpacing(10)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(self.theme_name)
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        self.theme_combo.setFont(make_font(MONO_STACK, 8))
        bar.addWidget(self.theme_combo)

        self.mode_badge = QLabel("VIEWER")
        self.mode_badge.setObjectName("ModeBadge")
        self.mode_badge.setFont(self._spaced_font(MONO_STACK, 8, bold=True, spacing=120))
        bar.addWidget(self.mode_badge)

        root_layout.addWidget(self.toolbar)

        rule = QFrame()
        rule.setObjectName("ToolbarRule")
        rule.setFixedHeight(1)
        root_layout.addWidget(rule)

        # ---- Search bar (hidden until Ctrl+F) ------------------------------------
        self.search_bar = QFrame()
        self.search_bar.setObjectName("SearchBar")
        search_layout = QHBoxLayout(self.search_bar)
        search_layout.setContentsMargins(14, 6, 14, 6)
        search_layout.setSpacing(10)

        find_label = QLabel("FIND")
        find_label.setObjectName("PaneHeader")
        find_label.setFont(self._spaced_font(UI_STACK, 8, bold=True, spacing=180))
        search_layout.addWidget(find_label)

        self.search_input = QLineEdit()
        self.search_input.setFont(make_font(MONO_STACK, 10))
        self.search_input.setFixedWidth(320)
        self.search_input.setPlaceholderText("search document…")
        self.search_input.textChanged.connect(self.do_search)
        self.search_input.returnPressed.connect(self.next_match)
        search_layout.addWidget(self.search_input)

        self.search_result_label = QLabel("")
        self.search_result_label.setObjectName("SearchResult")
        self.search_result_label.setFont(make_font(MONO_STACK, 8))
        search_layout.addWidget(self.search_result_label)

        search_layout.addStretch(1)

        self.search_close_button = self._tool_button("✕", self.close_search)
        self.search_close_button.setFixedWidth(30)
        search_layout.addWidget(self.search_close_button)

        self.search_bar.setVisible(False)
        root_layout.addWidget(self.search_bar)

        # ---- Panes ---------------------------------------------------------------
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(2)
        root_layout.addWidget(self.main_splitter, 1)

        toc_pane, toc_layout = self._pane("STRUCTURE")
        self.toc_list = QListWidget()
        self.toc_list.setFont(make_font(MONO_STACK, 9))
        self.toc_list.itemClicked.connect(self.on_heading_selected)
        toc_layout.addWidget(self.toc_list, 1)
        self.main_splitter.addWidget(toc_pane)

        preview_pane, preview_layout = self._pane("PREVIEW")
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.preview.setFont(make_font(UI_STACK, 10))
        preview_layout.addWidget(self.preview, 1)
        self.main_splitter.addWidget(preview_pane)

        self.main_splitter.setSizes([250, 930])

        # ---- Status bar ------------------------------------------------------------
        self.status_frame = QFrame()
        self.status_frame.setObjectName("StatusBar")
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(14, 5, 14, 5)

        self.status_label = QLabel("READY")
        self.status_label.setFont(make_font(MONO_STACK, 8))
        status_layout.addWidget(self.status_label, 1)

        self.refresh_dot = QLabel("● AUTO-REFRESHED")
        self.refresh_dot.setObjectName("RefreshDot")
        self.refresh_dot.setFont(make_font(MONO_STACK, 8))
        self.refresh_dot.setVisible(False)
        status_layout.addWidget(self.refresh_dot)

        self.stats_label = QLabel("")
        self.stats_label.setObjectName("StatsLabel")
        self.stats_label.setFont(make_font(MONO_STACK, 8))
        status_layout.addWidget(self.stats_label)

        root_layout.addWidget(self.status_frame)

    def _tool_button(self, text: str, slot) -> QPushButton:
        button = QPushButton(text)
        button.setFont(self._spaced_font(MONO_STACK, 8, bold=True, spacing=110))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(slot)
        return button

    def _pane(self, header_text: str):
        pane = QFrame()
        pane.setObjectName("Pane")
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QLabel(header_text)
        header.setObjectName("PaneHeader")
        header.setFont(self._spaced_font(UI_STACK, 8, bold=True, spacing=180))
        layout.addWidget(header)
        return pane, layout

    @staticmethod
    def _spaced_font(families: List[str], size: int, bold: bool = False,
                     spacing: int = 100) -> QFont:
        font = make_font(families, size, bold)
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, spacing)
        return font

    def bind_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.choose_and_open_file)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.refresh)
        QShortcut(QKeySequence("F5"), self, activated=self.refresh)
        QShortcut(QKeySequence("Ctrl+T"), self, activated=self.cycle_theme)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.open_search)
        QShortcut(QKeySequence("Escape"), self, activated=self.close_search)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self.print_document)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=self.close)
        QShortcut(QKeySequence("F11"), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence("Ctrl+="), self, activated=lambda: self.adjust_zoom(0.1))
        QShortcut(QKeySequence("Ctrl+-"), self, activated=lambda: self.adjust_zoom(-0.1))
        QShortcut(QKeySequence("Ctrl+0"), self, activated=self.reset_zoom)

    # --------------------------------------------------------------------------
    # Drag & drop
    # --------------------------------------------------------------------------

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self.load_file(path)
                break

    # --------------------------------------------------------------------------
    # Theming
    # --------------------------------------------------------------------------

    def apply_theme(self) -> None:
        t = THEMES[self.theme_combo.currentText()]
        self.theme = t
        self.setStyleSheet(self.build_qss(t))
        self.preview.document().setDefaultStyleSheet(self.build_preview_css(t, self.zoom))
        if self.file_path:
            self.render()
        else:
            self.show_welcome()

    def on_theme_changed(self, name: str) -> None:
        self.apply_theme()
        self.set_status(f"THEME // {name.upper()}")

    def cycle_theme(self) -> None:
        names = list(THEMES.keys())
        current = self.theme_combo.currentText()
        next_name = names[(names.index(current) + 1) % len(names)]
        self.theme_combo.setCurrentText(next_name)

    @staticmethod
    def build_qss(t: Dict[str, str]) -> str:
        return f"""
        QMainWindow, QWidget {{
            background: {t["bg"]};
            color: {t["fg"]};
        }}
        #Toolbar, #SearchBar {{
            background: {t["panel"]};
        }}
        #SearchBar {{
            border-bottom: 1px solid {t["border"]};
        }}
        #ToolbarRule {{
            background: {t["accent"]};
            border: none;
        }}
        #AppMark {{
            color: {t["accent"]};
        }}
        #PathLabel, #ZoomLabel {{
            color: {t["muted"]};
        }}
        #SearchResult {{
            color: {t["accent"]};
        }}
        #ModeBadge {{
            color: {t["accent2"]};
            border: 1px solid {t["accent2"]};
            border-radius: 2px;
            padding: 3px 10px;
            background: transparent;
        }}
        #Pane {{
            background: {t["bg"]};
            border: none;
        }}
        #PaneHeader {{
            color: {t["muted"]};
        }}
        QPushButton {{
            background: {t["panel2"]};
            color: {t["fg"]};
            border: 1px solid {t["border"]};
            border-radius: 2px;
            padding: 5px 14px;
        }}
        QPushButton:hover {{
            border-color: {t["accent"]};
            color: {t["accent"]};
        }}
        QPushButton:pressed {{
            background: {t["select_bg"]};
        }}
        QPushButton:disabled {{
            color: {t["gutter_fg"]};
            border-color: {t["panel2"]};
        }}
        QLineEdit {{
            background: {t["editor_bg"]};
            color: {t["fg"]};
            border: 1px solid {t["border"]};
            border-radius: 2px;
            padding: 4px 8px;
            selection-background-color: {t["select_bg"]};
            selection-color: {t["select_fg"]};
        }}
        QLineEdit:focus {{
            border-color: {t["accent"]};
        }}
        QComboBox {{
            background: {t["panel2"]};
            color: {t["fg"]};
            border: 1px solid {t["border"]};
            border-radius: 2px;
            padding: 4px 10px;
        }}
        QComboBox:hover {{
            border-color: {t["accent"]};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 18px;
        }}
        QComboBox QAbstractItemView {{
            background: {t["panel"]};
            color: {t["fg"]};
            border: 1px solid {t["border"]};
            selection-background-color: {t["select_bg"]};
            selection-color: {t["select_fg"]};
            outline: none;
        }}
        QMenu {{
            background: {t["panel"]};
            color: {t["fg"]};
            border: 1px solid {t["border"]};
            padding: 4px;
        }}
        QMenu::item {{
            padding: 5px 18px;
            border-radius: 2px;
        }}
        QMenu::item:selected {{
            background: {t["select_bg"]};
            color: {t["accent"]};
        }}
        QMenu::separator {{
            height: 1px;
            background: {t["border"]};
            margin: 4px 8px;
        }}
        QTextBrowser {{
            background: {t["bg"]};
            color: {t["fg"]};
            border: 1px solid {t["border"]};
            border-radius: 3px;
            padding: 6px;
            selection-background-color: {t["select_bg"]};
            selection-color: {t["select_fg"]};
        }}
        QListWidget {{
            background: {t["panel2"]};
            color: {t["fg"]};
            border: 1px solid {t["border"]};
            border-radius: 3px;
            padding: 4px;
            outline: none;
        }}
        QListWidget::item {{
            padding: 4px 6px;
            border-radius: 2px;
        }}
        QListWidget::item:hover {{
            background: {t["panel"]};
            color: {t["accent"]};
        }}
        QListWidget::item:selected {{
            background: {t["select_bg"]};
            color: {t["select_fg"]};
            border-left: 2px solid {t["accent"]};
        }}
        QSplitter::handle {{
            background: {t["border"]};
        }}
        QSplitter::handle:hover {{
            background: {t["accent"]};
        }}
        #StatusBar {{
            background: {t["panel"]};
            border-top: 1px solid {t["border"]};
        }}
        #StatusBar QLabel {{
            color: {t["muted"]};
        }}
        #StatsLabel {{
            color: {t["accent"]};
        }}
        #RefreshDot {{
            color: {t["accent2"]};
        }}
        QScrollBar:vertical {{
            background: {t["bg"]};
            width: 10px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {t["border"]};
            border-radius: 5px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t["accent"]};
        }}
        QScrollBar:horizontal {{
            background: {t["bg"]};
            height: 10px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {t["border"]};
            border-radius: 5px;
            min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {t["accent"]};
        }}
        QScrollBar::add-line, QScrollBar::sub-line {{
            height: 0;
            width: 0;
        }}
        QScrollBar::add-page, QScrollBar::sub-page {{
            background: transparent;
        }}
        QMessageBox {{
            background: {t["panel"]};
        }}
        """

    @staticmethod
    def build_preview_css(t: Dict[str, str], zoom: float = 1.0) -> str:
        mono = ", ".join(f"'{f}'" for f in MONO_STACK)

        def pt(base: float) -> str:
            return f"{base * zoom:.1f}pt"

        return f"""
        body {{
            color: {t["fg"]};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: {pt(10.5)};
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {t["accent2"]};
            margin-top: 16px;
            margin-bottom: 6px;
        }}
        h1 {{ font-size: {pt(18)}; }}
        h2 {{ font-size: {pt(15)}; }}
        h3 {{ font-size: {pt(12.5)}; }}
        p, li {{ color: {t["fg"]}; }}
        a {{ color: {t["link"]}; text-decoration: none; }}
        code {{
            font-family: {mono};
            color: {t["code_fg"]};
            background-color: {t["code_bg"]};
            font-size: {pt(9.5)};
        }}
        pre {{
            font-family: {mono};
            color: {t["code_fg"]};
            background-color: {t["code_bg"]};
            padding: 10px;
            font-size: {pt(9.5)};
        }}
        blockquote {{
            color: {t["muted"]};
            background-color: {t["quote_bg"]};
            margin: 8px 0px;
            padding: 6px 12px;
            border-left: 3px solid {t["quote_border"]};
        }}
        table {{ border-collapse: collapse; }}
        th, td {{
            border: 1px solid {t["border"]};
            padding: 6px 10px;
        }}
        th {{
            background-color: {t["panel"]};
            color: {t["accent"]};
        }}
        hr {{ color: {t["border"]}; background-color: {t["border"]}; }}
        .footnotes {{ color: {t["muted"]}; font-size: {pt(9)}; }}
        del {{ color: {t["muted"]}; }}
        """

    # --------------------------------------------------------------------------
    # Welcome screen
    # --------------------------------------------------------------------------

    def show_welcome(self) -> None:
        t = self.theme
        self.preview.document().setDefaultStyleSheet(self.build_preview_css(t, self.zoom))
        self.preview.setHtml(f"""
        <br><br><br><br><br><br>
        <div align="center">
            <p style="color:{t['accent']}; font-size:22pt;
                      font-family:'JetBrains Mono','Consolas',monospace;">MD//VIEW</p>
            <p style="color:{t['fg']}; font-size:12pt;"><b>No file open</b></p>
            <p style="color:{t['muted']};">Open a markdown file to start reading,<br>
            or drag &amp; drop one anywhere in this window.</p>
            <p style="color:{t['muted']}; font-size:8pt;
                      font-family:'JetBrains Mono','Consolas',monospace;">
            CTRL+O OPEN &nbsp;·&nbsp; CTRL+F FIND &nbsp;·&nbsp;
            CTRL+T THEME &nbsp;·&nbsp; CTRL+P PRINT</p>
        </div>
        """)
        self.toc_list.clear()
        placeholder = QListWidgetItem("(no document)")
        placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
        self.toc_list.addItem(placeholder)
        self.stats_label.setText("")

    # --------------------------------------------------------------------------
    # File operations
    # --------------------------------------------------------------------------

    def choose_and_open_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Markdown File", "",
                                                   MARKDOWN_FILE_FILTER)
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str) -> None:
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                QMessageBox.critical(self, "File Not Found", f"Could not find:\n{file_path}")
                return

            self.md_content = path_obj.read_text(encoding="utf-8")
            self.file_path = str(path_obj.resolve())
            self.file_mtime = path_obj.stat().st_mtime
            self.add_to_recent(self.file_path)

            self.render()
            self.update_window_title()
            self.update_path_label()
            self.watcher.start()
            self.set_status(f"LOADED // {self.file_path}")
        except UnicodeDecodeError:
            QMessageBox.critical(self, "Encoding Error", "This file is not valid UTF-8 text.")
        except Exception as exc:
            QMessageBox.critical(self, "Open Error", f"Could not open file.\n\n{exc}")

    def refresh(self) -> None:
        if not self.file_path:
            self.set_status("NO FILE LOADED")
            return
        self.load_file(self.file_path)
        self.set_status("REFRESHED")

    def check_file_changed(self) -> None:
        if not self.file_path:
            return
        try:
            mtime = Path(self.file_path).stat().st_mtime
        except OSError:
            return
        if mtime > self.file_mtime:
            self.file_mtime = mtime
            try:
                self.md_content = Path(self.file_path).read_text(encoding="utf-8")
            except Exception:
                return
            self.render()
            self.refresh_dot.setVisible(True)
            self.dot_timer.start()
            self.set_status("AUTO-REFRESHED // FILE CHANGED ON DISK")

    # --------------------------------------------------------------------------
    # Recent files
    # --------------------------------------------------------------------------

    @staticmethod
    def load_recent() -> List[str]:
        try:
            if RECENT_FILES_PATH.exists():
                data = json.loads(RECENT_FILES_PATH.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return [str(p) for p in data][:MAX_RECENT_FILES]
        except Exception:
            pass
        return []

    def save_recent(self) -> None:
        try:
            RECENT_FILES_PATH.write_text(json.dumps(self.recent_files), encoding="utf-8")
        except Exception:
            pass

    def add_to_recent(self, path: str) -> None:
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:MAX_RECENT_FILES]
        self.save_recent()

    def show_recent_menu(self) -> None:
        menu = QMenu(self)
        menu.setFont(make_font(MONO_STACK, 9))

        if self.recent_files:
            for path in self.recent_files:
                action = menu.addAction(Path(path).name)
                action.setToolTip(path)
                action.triggered.connect(lambda _checked=False, p=path: self.load_file(p))
            menu.addSeparator()
            clear = menu.addAction("CLEAR RECENT")
            clear.triggered.connect(self.clear_recent)
        else:
            empty = menu.addAction("(none)")
            empty.setEnabled(False)

        menu.exec(self.recent_button.mapToGlobal(
            self.recent_button.rect().bottomLeft()))

    def clear_recent(self) -> None:
        self.recent_files = []
        self.save_recent()
        self.set_status("RECENT FILES CLEARED")

    # --------------------------------------------------------------------------
    # Rendering
    # --------------------------------------------------------------------------

    def render(self) -> None:
        self.update_headings(self.md_content)
        body_html = self.render_markdown(self.md_content)

        if self.file_path:
            base = QUrl.fromLocalFile(str(Path(self.file_path).resolve().parent) + "/")
            self.preview.document().setBaseUrl(base)

        self.preview.document().setDefaultStyleSheet(
            self.build_preview_css(self.theme, self.zoom))

        scrollbar = self.preview.verticalScrollBar()
        scroll_pos = scrollbar.value()
        self.preview.setHtml(body_html)
        _ = self.preview.document().size()   # force full layout
        scrollbar.setValue(min(scroll_pos, scrollbar.maximum()))

        self.update_stats()
        if self.search_bar.isVisible() and self.search_input.text():
            self.do_search(self.search_input.text())

    def render_markdown(self, text: str) -> str:
        try:
            html = markdown2.markdown(text, extras=MARKDOWN_EXTRAS)
        except Exception as exc:
            return f"<h2>Markdown Render Error</h2><p>{self.escape_html(str(exc))}</p>"
        # QTextBrowser can't render <input> checkboxes from task lists —
        # swap them for unicode boxes.
        html = re.sub(r"<input[^>]*checked[^>]*>", "☑ ", html)
        html = re.sub(r"<input[^>]*type=[\"']checkbox[\"'][^>]*>", "☐ ", html)
        return html

    def update_stats(self) -> None:
        words = len(self.md_content.split())
        lines = self.md_content.count("\n") + 1 if self.md_content else 0
        self.stats_label.setText(
            f"{words:,} WORDS  •  {lines:,} LINES  •  {int(self.zoom * 100)}%")

    # --------------------------------------------------------------------------
    # Zoom
    # --------------------------------------------------------------------------

    def adjust_zoom(self, delta: float) -> None:
        self.zoom = max(0.6, min(1.8, round(self.zoom + delta, 2)))
        self.zoom_label.setText(f"{int(self.zoom * 100)}%")
        if self.file_path:
            self.render()
        else:
            self.show_welcome()
        self.set_status(f"ZOOM // {int(self.zoom * 100)}%")

    def reset_zoom(self) -> None:
        self.zoom = 1.0
        self.zoom_label.setText("100%")
        if self.file_path:
            self.render()
        else:
            self.show_welcome()
        self.set_status("ZOOM // RESET")

    # --------------------------------------------------------------------------
    # Fullscreen
    # --------------------------------------------------------------------------

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # --------------------------------------------------------------------------
    # Search
    # --------------------------------------------------------------------------

    def open_search(self) -> None:
        self.search_bar.setVisible(True)
        self.search_input.setFocus()
        self.search_input.selectAll()

    def close_search(self) -> None:
        if not self.search_bar.isVisible():
            return
        self.search_bar.setVisible(False)
        self.search_input.clear()
        self.preview.setExtraSelections([])
        self.search_matches = []
        self.search_index = -1

    def do_search(self, query: str) -> None:
        self.search_matches = []
        self.search_index = -1

        if not query:
            self.preview.setExtraSelections([])
            self.search_result_label.setText("")
            return

        doc = self.preview.document()
        highlight = QTextCharFormat()
        highlight.setBackground(QColor(self.theme["accent2"]))
        highlight.setForeground(QColor(self.theme["bg"]))

        selections = []
        cursor = QTextCursor(doc)
        while True:
            cursor = doc.find(query, cursor)
            if cursor.isNull():
                break
            self.search_matches.append(QTextCursor(cursor))
            selection = QTextEdit.ExtraSelection()
            selection.format = highlight
            selection.cursor = cursor
            selections.append(selection)

        self.preview.setExtraSelections(selections)
        count = len(self.search_matches)
        if count == 0:
            self.search_result_label.setText("NO MATCHES")
        else:
            self.search_result_label.setText(
                f"{count} MATCH{'ES' if count != 1 else ''}")
            self.next_match()

    def next_match(self) -> None:
        if not self.search_matches:
            return
        self.search_index = (self.search_index + 1) % len(self.search_matches)
        cursor = self.search_matches[self.search_index]
        self.preview.setTextCursor(cursor)
        self.preview.ensureCursorVisible()
        self.search_result_label.setText(
            f"{self.search_index + 1}/{len(self.search_matches)} MATCHES")

    # --------------------------------------------------------------------------
    # TOC / headings
    # --------------------------------------------------------------------------

    def update_headings(self, markdown_text: str) -> None:
        self.headings = self.extract_headings(markdown_text)
        self.toc_list.clear()

        if not self.headings:
            placeholder = QListWidgetItem("(no headings found)")
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            self.toc_list.addItem(placeholder)
            return

        for heading in self.headings:
            level = int(heading["level"])
            title = str(heading["title"])
            marker = "▸ " if level == 1 else "· "
            prefix = "  " * (level - 1)
            self.toc_list.addItem(QListWidgetItem(f"{prefix}{marker}{title}"))

    @staticmethod
    def extract_headings(markdown_text: str) -> List[Dict[str, object]]:
        headings: List[Dict[str, object]] = []
        in_fence = False

        for line_number, line in enumerate(markdown_text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
            if not match:
                continue

            level = len(match.group(1))
            raw_title = re.sub(r"\s+#+\s*$", "", match.group(2).strip())
            plain_title = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", raw_title)
            plain_title = plain_title.replace("`", "").strip()

            headings.append({
                "line": line_number,
                "level": level,
                "title": plain_title if plain_title else "(untitled heading)",
            })
        return headings

    def on_heading_selected(self, item: QListWidgetItem) -> None:
        index = self.toc_list.row(item)
        if not self.headings or index >= len(self.headings):
            return
        title = str(self.headings[index]["title"])
        found = self.preview.document().find(title)
        if not found.isNull():
            self.preview.setTextCursor(found)
            self.preview.ensureCursorVisible()
        self.set_status(f"JUMP // {title}")

    # --------------------------------------------------------------------------
    # Printing
    # --------------------------------------------------------------------------

    def print_document(self) -> None:
        if not self.file_path:
            self.set_status("NO FILE OPEN TO PRINT")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setDocName(Path(self.file_path).stem)

        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Print Document")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.set_status("PRINT // CANCELLED")
            return

        try:
            self._print_to(printer)
            self.set_status("PRINT // SENT TO PRINTER")
        except Exception as exc:
            QMessageBox.critical(self, "Print Error", f"Could not print.\n\n{exc}")

    def _print_to(self, printer: QPrinter) -> None:
        """Render a print-friendly copy and send it to `printer`.

        Always uses the daylight stylesheet at 100% zoom so dark themes
        don't print solid-colour page backgrounds.
        """
        doc = QTextDocument()
        doc.setDefaultStyleSheet(self.build_preview_css(THEMES["daylight"], 1.0))
        doc.setDefaultFont(make_font(UI_STACK, 10))
        if self.file_path:
            doc.setBaseUrl(QUrl.fromLocalFile(
                str(Path(self.file_path).resolve().parent) + "/"))
        doc.setHtml(self.render_markdown(self.md_content))
        doc.print(printer)

    # --------------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------------

    def update_window_title(self) -> None:
        name = Path(self.file_path).name if self.file_path else "No file open"
        self.setWindowTitle(f"{WINDOW_TITLE} — {name}")

    def update_path_label(self) -> None:
        if self.file_path:
            metrics = self.path_label.fontMetrics()
            elided = metrics.elidedText(self.file_path, Qt.TextElideMode.ElideLeft, 420)
            self.path_label.setText(elided)
            self.path_label.setToolTip(self.file_path)
        else:
            self.path_label.setText("NO FILE LOADED")
            self.path_label.setToolTip("")

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    @staticmethod
    def escape_html(text: str) -> str:
        return (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;"))


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main() -> None:
    theme_name = ARGS.theme if ARGS.theme else DEFAULT_THEME

    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)

    window = MarkdownViewerPro(
        startup_file=ARGS.file,
        theme_name=theme_name,
    )
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
