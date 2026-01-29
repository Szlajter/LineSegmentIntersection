import tkinter as tk
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

class CustomToolbar(NavigationToolbar2Tk):
    toolitems = [
        ('Back', 'Cofnij zmianę punktu', 'back', 'custom_undo'), 
        ('Forward', 'Ponów zmianę punktu', 'forward', 'custom_redo'),
        ('Save', 'Zapisz wykres', 'filesave', 'save_figure'),
    ]

    def __init__(self, canvas, window, app_instance):
        self.app = app_instance
        super().__init__(canvas, window)
        self.config(background="#2b2b2b")
        self._message_label.config(background="#2b2b2b", foreground="white")
        for button in self.winfo_children():
            if isinstance(button, tk.Button):
                button.config(background="#3a3a3a", foreground="white", borderwidth=0)

    def custom_undo(self): self.app.undo_action()
    def custom_redo(self): self.app.redo_action()