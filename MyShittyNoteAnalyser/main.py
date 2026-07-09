"""Entry point for the Note Analyzer application."""
import tkinter as tk
from gui import NoteAnalyzerApp

if __name__ == "__main__":
    root = tk.Tk()
    app = NoteAnalyzerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()