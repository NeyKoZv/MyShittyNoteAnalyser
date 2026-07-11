"""Entry point for the Note Analyzer application."""
import sys
from PyQt6.QtWidgets import QApplication
from gui import NoteAnalyzerApp

# Reuse the color constants for stylesheets
from constants import (COLOR_BG_DARK, COLOR_BG_DARKER, COLOR_BG_INPUT,
                       COLOR_FG_PRIMARY, COLOR_FG_SECONDARY,
                       COLOR_BUTTON_ACTIVE)

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLOR_BG_DARK};
}}
QWidget#CentralWidget {{
    background-color: {COLOR_BG_DARK};
}}
QGroupBox {{
    background-color: {COLOR_BG_DARK};
    color: {COLOR_FG_PRIMARY};
    border: 1px solid #444;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 14px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    color: {COLOR_FG_PRIMARY};
}}
QComboBox {{
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_FG_PRIMARY};
    border: 1px solid #555;
    border-radius: 3px;
    padding: 2px 6px;
}}
QComboBox::drop-down {{
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_FG_PRIMARY};
    selection-background-color: #555;
    selection-color: {COLOR_FG_PRIMARY};
}}
QSlider::groove:horizontal {{
    background: #555;
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {COLOR_FG_PRIMARY};
    width: 10px;
    height: 10px;
    margin: -4px 0;
    border-radius: 5px;
}}
QCheckBox {{
    color: {COLOR_FG_PRIMARY};
    background: transparent;
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid #888;
    border-radius: 3px;
    background: #333;
}}
QCheckBox::indicator:checked {{
    background: #00cc66;
    border: 2px solid #00ff88;
}}
QCheckBox::indicator:hover {{
    border-color: #aaa;
}}
QSpinBox {{
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_FG_PRIMARY};
    border: 1px solid #555;
    border-radius: 3px;
    padding: 1px 4px;
}}
QPushButton {{
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_FG_PRIMARY};
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px 12px;
}}
QPushButton:hover {{
    background-color: {COLOR_BUTTON_ACTIVE};
}}
QPushButton:pressed {{
    background-color: #555;
}}
QScrollBar:horizontal {{
    background: {COLOR_BG_DARK};
    height: 12px;
}}
QScrollBar::handle:horizontal {{
    background: #555;
    min-width: 20px;
    border-radius: 6px;
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
}}
QLabel {{
    color: {COLOR_FG_PRIMARY};
    background: transparent;
}}"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Note Analyzer")
    app.setStyleSheet(STYLESHEET)
    window = NoteAnalyzerApp()
    window.show()
    app.exec()