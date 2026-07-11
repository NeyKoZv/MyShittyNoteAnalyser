"""Entry point for the Note Analyzer application."""
import sys
from PyQt6.QtWidgets import QApplication
from gui import NoteAnalyzerApp
from theme import STYLESHEET

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Note Analyzer")
    app.setStyleSheet(STYLESHEET)
    window = NoteAnalyzerApp()
    window.show()
    app.exec()