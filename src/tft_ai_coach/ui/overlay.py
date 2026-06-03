from __future__ import annotations

import tkinter as tk


class CoachOverlay:
    def __init__(self, parent: tk.Tk) -> None:
        self.parent = parent
        self.window: tk.Toplevel | None = None
        self.label: tk.Label | None = None

    def show(self) -> None:
        if self.window is not None:
            self.window.deiconify()
            return
        window = tk.Toplevel(self.parent)
        window.title("TFT Coach Overlay")
        window.geometry("360x170+40+120")
        window.attributes("-topmost", True)
        window.attributes("-alpha", 0.92)
        window.configure(bg="#111318")
        window.protocol("WM_DELETE_WINDOW", self.hide)
        self.label = tk.Label(
            window,
            text="Aguardando recomendacao...",
            justify="left",
            anchor="nw",
            bg="#111318",
            fg="#f3f6fb",
            padx=14,
            pady=12,
            font=("Segoe UI", 10),
        )
        self.label.pack(fill="both", expand=True)
        self.window = window

    def hide(self) -> None:
        if self.window is not None:
            self.window.withdraw()

    def update_text(self, text: str) -> None:
        if self.window is None:
            return
        if self.label is not None:
            self.label.configure(text=text)

