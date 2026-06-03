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
        screen_width = self.parent.winfo_screenwidth()
        x = max(20, screen_width - 470)
        window.geometry(f"440x292+{x}+84")
        window.attributes("-topmost", True)
        window.attributes("-alpha", 0.94)
        window.overrideredirect(True)
        window.configure(bg="#18142d")
        window.protocol("WM_DELETE_WINDOW", self.hide)
        header = tk.Label(
            window,
            text="TFT AI COACH",
            anchor="w",
            bg="#211a42",
            fg="#ffd84d",
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        header.pack(fill="x")
        self.label = tk.Label(
            window,
            text="Aguardando leitura ao vivo...",
            justify="left",
            anchor="nw",
            bg="#18142d",
            fg="#f3f6fb",
            padx=12,
            pady=10,
            font=("Consolas", 9),
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
