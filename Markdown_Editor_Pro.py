#!/usr/bin/env python3
"""
Markdown Editor Pro — PyQt6 Edition
====================================
A dark-industrial markdown editor / viewer.

    python Markdown_Editor_Pro.py [file] [--mode editor|viewer] [--theme obsidian|phosphor|daylight]

Copyright (c) 2026 Leon Priest (7h3v01d)
Licensed under the Apache License, Version 2.0
"""

import sys
import re
import argparse
import importlib.util
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# ==============================================================================
# CONFIGURATION
# ==============================================================================

APP_MODE = "editor"            # "editor" | "viewer"
DEFAULT_THEME = "obsidian"     # "obsidian" | "phosphor" | "daylight"
LIVE_PREVIEW_DELAY_MS = 450
WINDOW_TITLE = "Markdown Editor Pro"
MONO_STACK = ["JetBrains Mono", "Cascadia Code", "Consolas", "Courier New"]
UI_STACK = ["Segoe UI", "Inter", "Arial"]

REQUIRED_DEPENDENCIES = {
    "markdown2": "markdown2>=2.4.0",
    "PyQt6": "PyQt6>=6.4.0",
}

# ------------------------------------------------------------------------------
# Themes: navy/teal/amber industrial (default), phosphor terminal, and light.
# ------------------------------------------------------------------------------

THEMES: Dict[str, Dict[str, str]] = {
    "obsidian": {
        "bg":           "#0b1220",   # deep navy
        "panel":        "#101a2c",
        "panel2":       "#0e1626",
        "border":       "#1e2f4a",
        "fg":           "#d7e2f0",
        "muted":        "#6b7f9c",
        "accent":       "#2dd4bf",   # teal
        "accent2":      "#f5a524",   # amber
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
    parser.add_argument("--mode", choices=["editor", "viewer"], help="Override APP_MODE.")
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
from PyQt6.QtCore import (  # noqa: E402
    Qt, QTimer, QSize, QRect, QRegularExpression, QUrl,
)
from PyQt6.QtGui import (  # noqa: E402
    QFont, QColor, QPainter, QTextFormat, QTextCharFormat,
    QSyntaxHighlighter, QKeySequence, QShortcut, QTextCursor, QTextDocument,
)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog  # noqa: E402
from PyQt6.QtWidgets import (  # noqa: E402
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QComboBox, QSplitter, QListWidget, QListWidgetItem,
    QPlainTextEdit, QTextEdit, QTextBrowser, QFrame, QFileDialog, QMessageBox,
    QSizePolicy, QDialog,
)


def make_font(families: List[str], size: int, bold: bool = False) -> QFont:
    font = QFont()
    font.setFamilies(families)
    font.setPointSize(size)
    font.setBold(bold)
    return font


# ==============================================================================
# SYNTAX HIGHLIGHTER
# ==============================================================================

class MarkdownHighlighter(QSyntaxHighlighter):
    """Lightweight markdown highlighting tuned for the industrial themes."""

    FENCE_STATE = 1

    def __init__(self, document, theme: Dict[str, str]) -> None:
        super().__init__(document)
        self.rules: List[tuple] = []
        self.fence_format = QTextCharFormat()
        self.fence_re = QRegularExpression(r"^(\s*)(```|~~~)")
        self.set_theme(theme)

    def set_theme(self, theme: Dict[str, str]) -> None:
        def fmt(color: str, bold: bool = False, italic: bool = False,
                bg: Optional[str] = None) -> QTextCharFormat:
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bg:
                f.setBackground(QColor(bg))
            if bold:
                f.setFontWeight(QFont.Weight.Bold)
            if italic:
                f.setFontItalic(True)
            return f

        self.rules = [
            # Headings — amber, bold
            (QRegularExpression(r"^#{1,6}\s.*$"), fmt(theme["accent2"], bold=True)),
            # Bold / italic
            (QRegularExpression(r"\*\*[^*\n]+\*\*|__[^_\n]+__"), fmt(theme["fg"], bold=True)),
            (QRegularExpression(r"(?<![\w*])\*[^*\n]+\*(?![\w*])|(?<![\w_])_[^_\n]+_(?![\w_])"),
             fmt(theme["fg"], italic=True)),
            # Inline code — teal on code background
            (QRegularExpression(r"`[^`\n]+`"), fmt(theme["code_fg"], bg=theme["code_bg"])),
            # Links / images
            (QRegularExpression(r"!?\[[^\]\n]*\]\([^)\n]*\)"), fmt(theme["link"])),
            # Blockquotes
            (QRegularExpression(r"^\s*>.*$"), fmt(theme["muted"], italic=True)),
            # List markers
            (QRegularExpression(r"^\s*([-+*]|\d+\.)\s"), fmt(theme["accent"], bold=True)),
            # Horizontal rules
            (QRegularExpression(r"^\s*([-*_])\s*(\1\s*){2,}$"), fmt(theme["border"])),
        ]
        self.fence_format = fmt(theme["code_fg"], bg=theme["code_bg"])
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        fence_match = self.fence_re.match(text)
        prev_in_fence = self.previousBlockState() == self.FENCE_STATE

        if prev_in_fence:
            self.setFormat(0, len(text), self.fence_format)
            if fence_match.hasMatch():
                self.setCurrentBlockState(0)      # closing fence
            else:
                self.setCurrentBlockState(self.FENCE_STATE)
            return

        if fence_match.hasMatch():
            self.setFormat(0, len(text), self.fence_format)
            self.setCurrentBlockState(self.FENCE_STATE)
            return

        self.setCurrentBlockState(0)
        for regex, char_format in self.rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), char_format)


# ==============================================================================
# EDITOR WITH LINE-NUMBER GUTTER
# ==============================================================================

class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor") -> None:
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.editor.gutter_width(), 0)

    def paintEvent(self, event) -> None:
        self.editor.paint_gutter(event)


class CodeEditor(QPlainTextEdit):
    """QPlainTextEdit with a line-number gutter and current-line highlight."""

    def __init__(self, theme: Dict[str, str]) -> None:
        super().__init__()
        self.theme = theme
        self.gutter = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_gutter_width)
        self.updateRequest.connect(self.on_update_request)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.update_gutter_width()
        self.highlight_current_line()

    def set_theme(self, theme: Dict[str, str]) -> None:
        self.theme = theme
        self.highlight_current_line()
        self.gutter.update()

    def gutter_width(self) -> int:
        digits = max(3, len(str(max(1, self.blockCount()))))
        return 18 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_gutter_width(self, _block_count: int = 0) -> None:
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def on_update_request(self, rect: QRect, dy: int) -> None:
        if dy:
            self.gutter.scroll(0, dy)
        else:
            self.gutter.update(0, rect.y(), self.gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_gutter_width()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.gutter.setGeometry(QRect(cr.left(), cr.top(), self.gutter_width(), cr.height()))

    def paint_gutter(self, event) -> None:
        painter = QPainter(self.gutter)
        painter.fillRect(event.rect(), QColor(self.theme["gutter_bg"]))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        current_line = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                if block_number == current_line:
                    painter.setPen(QColor(self.theme["accent"]))
                else:
                    painter.setPen(QColor(self.theme["gutter_fg"]))
                painter.drawText(
                    0, top, self.gutter.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self) -> None:
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(self.theme["cursor_line"]))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])
        self.gutter.update()


# ==============================================================================
# MAIN WINDOW
# ==============================================================================

class MarkdownEditorPro(QMainWindow):
    def __init__(self, startup_file: Optional[str], mode: str, theme_name: str) -> None:
        super().__init__()
        self.mode = mode
        self.read_only = (mode == "viewer")
        self.theme_name = theme_name if theme_name in THEMES else DEFAULT_THEME
        self.theme = THEMES[self.theme_name]

        self.file_path: Optional[str] = None
        self.last_saved_text: str = ""
        self.headings: List[Dict[str, object]] = []
        self.editor_font_size = 11
        self._syncing_scroll = False

        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(LIVE_PREVIEW_DELAY_MS)
        self.preview_timer.timeout.connect(self.refresh_preview)

        self.build_ui()
        self.bind_shortcuts()
        self.apply_theme()

        self.resize(1400, 900)
        self.setMinimumSize(980, 640)

        if startup_file:
            self.open_file(startup_file)
        else:
            self.refresh_preview(initial=True)
        self.update_title()

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

        self.app_label = QLabel("MD//PRO")
        self.app_label.setObjectName("AppMark")
        self.app_label.setFont(self._spaced_font(MONO_STACK, 12, bold=True, spacing=140))
        bar.addWidget(self.app_label)

        bar.addSpacing(10)

        self.open_button = self._tool_button("OPEN", self.choose_and_open_file)
        self.reload_button = self._tool_button("RELOAD", self.reload_file)
        self.save_button = self._tool_button("SAVE", self.save_file)
        self.save_as_button = self._tool_button("SAVE AS", self.save_file_as)
        self.refresh_button = self._tool_button("REFRESH", self.refresh_preview)
        self.print_button = self._tool_button("PRINT", self.print_preview_pane)
        for button in (self.open_button, self.reload_button, self.save_button,
                       self.save_as_button, self.refresh_button, self.print_button):
            bar.addWidget(button)

        bar.addSpacing(12)

        if not self.read_only:
            self.live_preview_check = QCheckBox("LIVE PREVIEW")
            self.live_preview_check.setChecked(True)
            self.live_preview_check.setFont(self._spaced_font(UI_STACK, 8, spacing=110))
            self.live_preview_check.toggled.connect(self.on_live_preview_toggle)
            bar.addWidget(self.live_preview_check)

            self.sync_scroll_check = QCheckBox("SYNC SCROLL")
            self.sync_scroll_check.setChecked(True)
            self.sync_scroll_check.setFont(self._spaced_font(UI_STACK, 8, spacing=110))
            self.sync_scroll_check.toggled.connect(self.on_sync_scroll_toggle)
            bar.addWidget(self.sync_scroll_check)
        else:
            self.live_preview_check = None
            self.sync_scroll_check = None
            self.save_button.setEnabled(False)
            self.save_as_button.setEnabled(False)

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

        self.mode_badge = QLabel("VIEWER" if self.read_only else "EDITOR")
        self.mode_badge.setObjectName("ModeBadge")
        self.mode_badge.setFont(self._spaced_font(MONO_STACK, 8, bold=True, spacing=120))
        bar.addWidget(self.mode_badge)

        root_layout.addWidget(self.toolbar)

        rule = QFrame()
        rule.setObjectName("ToolbarRule")
        rule.setFixedHeight(1)
        root_layout.addWidget(rule)

        # ---- Panes -------------------------------------------------------------
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(2)
        root_layout.addWidget(self.main_splitter, 1)

        if not self.read_only:
            editor_pane, editor_layout = self._pane("SOURCE")
            self.editor = CodeEditor(self.theme)
            self.editor.setFont(make_font(MONO_STACK, self.editor_font_size))
            editor_layout.addWidget(self.editor, 1)
            self.highlighter = MarkdownHighlighter(self.editor.document(), self.theme)
            self.main_splitter.addWidget(editor_pane)
        else:
            self.editor = None
            self.highlighter = None

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

        if self.read_only:
            self.main_splitter.setSizes([260, 900])
        else:
            self.main_splitter.setSizes([560, 220, 620])

        # ---- Status bar ----------------------------------------------------------
        self.status_frame = QFrame()
        self.status_frame.setObjectName("StatusBar")
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(14, 5, 14, 5)

        self.status_label = QLabel("READY")
        self.status_label.setFont(make_font(MONO_STACK, 8))
        status_layout.addWidget(self.status_label, 1)

        self.stats_label = QLabel("")
        self.stats_label.setObjectName("StatsLabel")
        self.stats_label.setFont(make_font(MONO_STACK, 8))
        status_layout.addWidget(self.stats_label)

        root_layout.addWidget(self.status_frame)

        # Signal hookups last — the highlighter's initial rehighlight can emit
        # textChanged, so these must not fire before the status bar exists.
        if self.editor is not None:
            self.editor.textChanged.connect(self.on_editor_modified)
            self.editor.cursorPositionChanged.connect(self.update_stats)
            self.editor.verticalScrollBar().valueChanged.connect(self.sync_from_editor)
            self.preview.verticalScrollBar().valueChanged.connect(self.sync_from_preview)
            # Both widgets lay out lazily, so scrollbar ranges settle after the
            # initial sync fires. Re-align (editor as source of truth) whenever
            # either range changes; the guard flag prevents feedback loops.
            self.editor.verticalScrollBar().rangeChanged.connect(
                lambda *_: self.sync_from_editor())
            self.preview.verticalScrollBar().rangeChanged.connect(
                lambda *_: self.sync_from_editor())
        self.update_stats()

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
        QShortcut(QKeySequence("F5"), self, activated=self.refresh_preview)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.reload_file)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self.print_preview_pane)
        QShortcut(QKeySequence("Ctrl+="), self, activated=lambda: self.adjust_font(1))
        QShortcut(QKeySequence("Ctrl+-"), self, activated=lambda: self.adjust_font(-1))
        if not self.read_only:
            QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_file)
            QShortcut(QKeySequence("Ctrl+Shift+S"), self, activated=self.save_file_as)

    def adjust_font(self, delta: int) -> None:
        self.editor_font_size = max(7, min(24, self.editor_font_size + delta))
        if self.editor is not None:
            self.editor.setFont(make_font(MONO_STACK, self.editor_font_size))
        self.set_status(f"EDITOR FONT {self.editor_font_size}pt")

    # --------------------------------------------------------------------------
    # Theming
    # --------------------------------------------------------------------------

    def apply_theme(self) -> None:
        t = THEMES[self.theme_combo.currentText()]
        self.theme = t
        self.setStyleSheet(self.build_qss(t))

        if self.editor is not None:
            self.editor.set_theme(t)
        if self.highlighter is not None:
            self.highlighter.set_theme(t)

        self.preview.document().setDefaultStyleSheet(self.build_preview_css(t))
        self.refresh_preview()

    def on_theme_changed(self, name: str) -> None:
        self.apply_theme()
        self.set_status(f"THEME // {name.upper()}")

    @staticmethod
    def build_qss(t: Dict[str, str]) -> str:
        return f"""
        QMainWindow, QWidget {{
            background: {t["bg"]};
            color: {t["fg"]};
        }}
        #Toolbar {{
            background: {t["panel"]};
        }}
        #ToolbarRule {{
            background: {t["accent"]};
            border: none;
        }}
        #AppMark {{
            color: {t["accent"]};
        }}
        #PathLabel {{
            color: {t["muted"]};
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
        QCheckBox {{
            color: {t["muted"]};
            spacing: 6px;
        }}
        QCheckBox:checked {{
            color: {t["accent"]};
        }}
        QCheckBox::indicator {{
            width: 12px;
            height: 12px;
            border: 1px solid {t["border"]};
            border-radius: 2px;
            background: {t["panel2"]};
        }}
        QCheckBox::indicator:checked {{
            background: {t["accent"]};
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
        QPlainTextEdit {{
            background: {t["editor_bg"]};
            color: {t["fg"]};
            border: 1px solid {t["border"]};
            border-radius: 3px;
            selection-background-color: {t["select_bg"]};
            selection-color: {t["select_fg"]};
        }}
        QPlainTextEdit:focus {{
            border-color: {t["accent"]};
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
    def build_preview_css(t: Dict[str, str]) -> str:
        mono = ", ".join(f"'{f}'" for f in MONO_STACK)
        return f"""
        body {{
            color: {t["fg"]};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10.5pt;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {t["accent2"]};
            margin-top: 16px;
            margin-bottom: 6px;
        }}
        h1 {{ font-size: 18pt; }}
        h2 {{ font-size: 15pt; }}
        h3 {{ font-size: 12.5pt; }}
        p, li {{ color: {t["fg"]}; }}
        a {{ color: {t["link"]}; text-decoration: none; }}
        code {{
            font-family: {mono};
            color: {t["code_fg"]};
            background-color: {t["code_bg"]};
            font-size: 9.5pt;
        }}
        pre {{
            font-family: {mono};
            color: {t["code_fg"]};
            background-color: {t["code_bg"]};
            padding: 10px;
            font-size: 9.5pt;
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
        """

    # --------------------------------------------------------------------------
    # File operations
    # --------------------------------------------------------------------------

    def choose_and_open_file(self) -> None:
        if not self.confirm_discard_unsaved_changes():
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Markdown File", "",
                                                   MARKDOWN_FILE_FILTER)
        if file_path:
            self.open_file(file_path)

    def open_file(self, file_path: str) -> None:
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                QMessageBox.critical(self, "File Not Found", f"Could not find:\n{file_path}")
                return

            text = path_obj.read_text(encoding="utf-8")
            self.file_path = str(path_obj.resolve())
            self.last_saved_text = text

            if self.editor is not None:
                self.editor.blockSignals(True)
                self.editor.setPlainText(text)
                self.editor.blockSignals(False)
                self.editor.document().setModified(False)

            self.update_title()
            self.update_path_label()
            self.refresh_preview()
            self.set_status(f"LOADED // {self.file_path}")
        except UnicodeDecodeError:
            QMessageBox.critical(self, "Encoding Error", "This file is not valid UTF-8 text.")
        except Exception as exc:
            QMessageBox.critical(self, "Open Error", f"Could not open file.\n\n{exc}")

    def reload_file(self) -> None:
        if not self.file_path:
            self.set_status("NO FILE LOADED TO RELOAD")
            return
        if not self.confirm_discard_unsaved_changes():
            return
        self.open_file(self.file_path)

    def save_file(self) -> None:
        if self.read_only:
            self.set_status("READ-ONLY MODE // SAVE DISABLED")
            return
        if not self.file_path:
            self.save_file_as()
            return
        try:
            text = self.get_markdown_text()
            Path(self.file_path).write_text(text, encoding="utf-8")
            self.last_saved_text = text
            if self.editor is not None:
                self.editor.document().setModified(False)
            self.update_title()
            self.refresh_preview()
            self.set_status(f"SAVED // {self.file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", f"Could not save file.\n\n{exc}")

    def save_file_as(self) -> None:
        if self.read_only:
            self.set_status("READ-ONLY MODE // SAVE AS DISABLED")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Markdown File", "",
                                                   MARKDOWN_FILE_FILTER)
        if not file_path:
            return
        if not Path(file_path).suffix:
            file_path += ".md"
        self.file_path = file_path
        self.save_file()
        self.update_path_label()

    # --------------------------------------------------------------------------
    # Editor / state handling
    # --------------------------------------------------------------------------

    def get_markdown_text(self) -> str:
        if self.editor is not None:
            return self.editor.toPlainText()
        return self.last_saved_text

    def on_editor_modified(self) -> None:
        self.update_title()
        self.update_stats()
        if self.live_preview_check is not None and self.live_preview_check.isChecked():
            self.preview_timer.start()

    def on_live_preview_toggle(self, checked: bool) -> None:
        if checked:
            self.preview_timer.start()
            self.set_status("LIVE PREVIEW // ON")
        else:
            self.preview_timer.stop()
            self.set_status("LIVE PREVIEW // OFF")

    # --------------------------------------------------------------------------
    # Scroll sync
    # --------------------------------------------------------------------------

    def sync_scroll_enabled(self) -> bool:
        return (self.sync_scroll_check is not None
                and self.sync_scroll_check.isChecked()
                and self.editor is not None)

    def on_sync_scroll_toggle(self, checked: bool) -> None:
        if checked:
            self.sync_from_editor()   # snap panes into alignment immediately
            self.set_status("SYNC SCROLL // ON")
        else:
            self.set_status("SYNC SCROLL // OFF")

    @staticmethod
    def _sync_scrollbars(source, target) -> None:
        source_max = source.maximum()
        if source_max <= 0:
            return
        fraction = source.value() / source_max
        target.setValue(round(fraction * target.maximum()))

    def sync_from_editor(self, _value: int = 0) -> None:
        if self._syncing_scroll or not self.sync_scroll_enabled():
            return
        self._syncing_scroll = True
        try:
            self._sync_scrollbars(self.editor.verticalScrollBar(),
                                  self.preview.verticalScrollBar())
        finally:
            self._syncing_scroll = False

    def sync_from_preview(self, _value: int = 0) -> None:
        if self._syncing_scroll or not self.sync_scroll_enabled():
            return
        self._syncing_scroll = True
        try:
            self._sync_scrollbars(self.preview.verticalScrollBar(),
                                  self.editor.verticalScrollBar())
        finally:
            self._syncing_scroll = False

    def has_unsaved_changes(self) -> bool:
        if self.read_only:
            return False
        return self.get_markdown_text() != self.last_saved_text

    def confirm_discard_unsaved_changes(self) -> bool:
        if self.read_only or not self.has_unsaved_changes():
            return True

        box = QMessageBox(self)
        box.setWindowTitle("Unsaved Changes")
        box.setText("You have unsaved changes.\n\nSave before continuing?")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )
        answer = box.exec()

        if answer == QMessageBox.StandardButton.Cancel:
            return False
        if answer == QMessageBox.StandardButton.Save:
            self.save_file()
            return not self.has_unsaved_changes()
        return True

    def update_title(self) -> None:
        dirty = " *" if self.has_unsaved_changes() else ""
        name = Path(self.file_path).name if self.file_path else "Untitled"
        mode = "Viewer" if self.read_only else "Editor"
        self.setWindowTitle(f"{WINDOW_TITLE} — {name}{dirty} [{mode}]")

    def update_path_label(self) -> None:
        if self.file_path:
            metrics = self.path_label.fontMetrics()
            elided = metrics.elidedText(self.file_path, Qt.TextElideMode.ElideLeft, 420)
            self.path_label.setText(elided)
            self.path_label.setToolTip(self.file_path)
        else:
            self.path_label.setText("NO FILE LOADED")
            self.path_label.setToolTip("")

    def update_stats(self) -> None:
        text = self.get_markdown_text()
        words = len(text.split())
        chars = len(text)
        if self.editor is not None:
            cursor = self.editor.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.positionInBlock() + 1
            self.stats_label.setText(f"LN {line}:{col}  •  {words} WORDS  •  {chars} CHARS")
        else:
            self.stats_label.setText(f"{words} WORDS  •  {chars} CHARS")

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    # --------------------------------------------------------------------------
    # Preview / rendering
    # --------------------------------------------------------------------------

    def refresh_preview(self, initial: bool = False) -> None:
        self.preview_timer.stop()
        markdown_text = self.get_markdown_text()
        self.update_headings(markdown_text)

        body_html = self.render_markdown(markdown_text)

        if self.file_path:
            base = QUrl.fromLocalFile(str(Path(self.file_path).resolve().parent) + "/")
            self.preview.document().setBaseUrl(base)

        scrollbar = self.preview.verticalScrollBar()
        scroll_pos = scrollbar.value()
        self._syncing_scroll = True
        try:
            self.preview.setHtml(body_html)
            # Force full document layout so the scrollbar range is final;
            # otherwise lazy layout makes proportional sync drift.
            _ = self.preview.document().size()
            scrollbar.setValue(min(scroll_pos, scrollbar.maximum()))
        finally:
            self._syncing_scroll = False

        if self.sync_scroll_enabled():
            self.sync_from_editor()

        if not initial:
            self.set_status("PREVIEW REFRESHED")

    def render_markdown(self, text: str) -> str:
        extras = ["fenced-code-blocks", "tables", "header-ids",
                  "code-friendly", "cuddled-lists"]
        kwargs = {"extras": extras}
        if self.read_only:
            kwargs["safe_mode"] = "escape"
        try:
            return markdown2.markdown(text, **kwargs)
        except Exception as exc:
            return f"<h2>Markdown Render Error</h2><p>{self.escape_html(str(exc))}</p>"

    # --------------------------------------------------------------------------
    # Printing
    # --------------------------------------------------------------------------

    def print_preview_pane(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        if self.file_path:
            printer.setDocName(Path(self.file_path).stem)

        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Print Preview Pane")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.set_status("PRINT // CANCELLED")
            return

        try:
            self._print_to(printer)
            self.set_status("PRINT // SENT TO PRINTER")
        except Exception as exc:
            QMessageBox.critical(self, "Print Error", f"Could not print.\n\n{exc}")

    def _print_to(self, printer: QPrinter) -> None:
        """Render a print-friendly copy of the preview and send it to `printer`.

        Always uses the daylight stylesheet so dark themes don't print
        solid-colour page backgrounds.
        """
        doc = QTextDocument()
        doc.setDefaultStyleSheet(self.build_preview_css(THEMES["daylight"]))
        doc.setDefaultFont(make_font(UI_STACK, 10))
        if self.file_path:
            doc.setBaseUrl(QUrl.fromLocalFile(
                str(Path(self.file_path).resolve().parent) + "/"))
        doc.setHtml(self.render_markdown(self.get_markdown_text()))
        doc.print(printer)

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

        heading = self.headings[index]
        line_number = int(heading["line"])
        title = str(heading["title"])

        if self.editor is not None:
            block = self.editor.document().findBlockByNumber(line_number - 1)
            if block.isValid():
                cursor = QTextCursor(block)
                self.editor.setTextCursor(cursor)
                self.editor.centerCursor()
                self.editor.setFocus()
            self.set_status(f"JUMP // {title} (LINE {line_number})")
        else:
            doc = self.preview.document()
            found = doc.find(title)
            if not found.isNull():
                self.preview.setTextCursor(found)
                self.preview.ensureCursorVisible()
            self.set_status(f"JUMP // {title}")

    # --------------------------------------------------------------------------
    # Helpers / shutdown
    # --------------------------------------------------------------------------

    @staticmethod
    def escape_html(text: str) -> str:
        return (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;"))

    def closeEvent(self, event) -> None:
        if self.confirm_discard_unsaved_changes():
            event.accept()
        else:
            event.ignore()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main() -> None:
    mode = ARGS.mode if ARGS.mode else APP_MODE
    theme_name = ARGS.theme if ARGS.theme else DEFAULT_THEME

    if mode not in {"editor", "viewer"}:
        print(f"Invalid APP_MODE: {mode!r}. Use 'editor' or 'viewer'.")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)

    window = MarkdownEditorPro(
        startup_file=ARGS.file,
        mode=mode,
        theme_name=theme_name,
    )
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
