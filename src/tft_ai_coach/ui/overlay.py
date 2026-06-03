from __future__ import annotations

import textwrap
import tkinter as tk

BG = "#101318"
SURFACE = "#171b22"
SURFACE_SOFT = "#1d232b"
TEXT = "#f4f1e8"
MUTED = "#9da7b3"
GOLD = "#d8b34a"
TEAL = "#62c7b4"
LINE = "#2b3340"
WARN = "#e6a04a"


class CoachOverlay:
    def __init__(self, parent: tk.Tk) -> None:
        self.parent = parent
        self.window: tk.Toplevel | None = None
        self._drag_start: tuple[int, int] | None = None
        self.status_var = tk.StringVar(value="live")
        self.comp_var = tk.StringVar(value="Aguardando leitura...")
        self.shop_var = tk.StringVar(value="Loja: aguardando")
        self.action_var = tk.StringVar(value="Agora: aguardando estado do jogo")
        self.economy_var = tk.StringVar(value="Economia: aguardando gold/level")
        self.augment_var = tk.StringVar(value="Augments: sem tela de augment")
        self.reason_var = tk.StringVar(value="")
        self.early_var = tk.StringVar(value="Early: -")
        self.mid_var = tk.StringVar(value="Mid: -")
        self.late_var = tk.StringVar(value="Late: -")

    def show(self) -> None:
        if self.window is not None:
            self.window.deiconify()
            return
        window = tk.Toplevel(self.parent)
        window.title("TFT Coach Overlay")
        screen_width = self.parent.winfo_screenwidth()
        x = max(20, screen_width - 452)
        window.geometry(f"424x318+{x}+78")
        window.attributes("-topmost", True)
        window.attributes("-alpha", 0.96)
        window.overrideredirect(True)
        window.configure(bg=BG)
        window.protocol("WM_DELETE_WINDOW", self.hide)

        shell = tk.Frame(window, bg=BG, highlightbackground=LINE, highlightthickness=1)
        shell.pack(fill="both", expand=True)

        header = tk.Frame(shell, bg=SURFACE, height=34)
        header.pack(fill="x")
        header.bind("<ButtonPress-1>", self._start_drag)
        header.bind("<B1-Motion>", self._drag)

        title = tk.Label(
            header,
            text="TFT AI Coach",
            anchor="w",
            bg=SURFACE,
            fg=TEXT,
            padx=12,
            font=("Segoe UI", 10, "bold"),
        )
        title.pack(side="left", fill="y")
        title.bind("<ButtonPress-1>", self._start_drag)
        title.bind("<B1-Motion>", self._drag)

        status = tk.Label(
            header,
            textvariable=self.status_var,
            bg="#242019",
            fg=GOLD,
            padx=8,
            pady=2,
            font=("Segoe UI", 8, "bold"),
        )
        status.pack(side="right", padx=(0, 10), pady=8)

        close = tk.Button(
            header,
            text="x",
            command=self.hide,
            bg=SURFACE,
            fg=MUTED,
            activebackground=SURFACE_SOFT,
            activeforeground=TEXT,
            borderwidth=0,
            padx=8,
            pady=0,
            font=("Segoe UI", 9, "bold"),
        )
        close.pack(side="right", fill="y")

        body = tk.Frame(shell, bg=BG, padx=10, pady=9)
        body.pack(fill="both", expand=True)

        self._label(
            body,
            self.comp_var,
            fg=GOLD,
            bg=BG,
            font=("Segoe UI", 12, "bold"),
            pady=(0, 7),
        )
        self._section(body, "Loja", self.shop_var, accent=TEAL)
        self._section(body, "Agora", self.action_var, accent=GOLD)
        self._section(body, "Economia", self.economy_var, accent=WARN)
        self._section(body, "Augments", self.augment_var, accent=TEAL)
        self._label(body, self.reason_var, fg=MUTED, bg=BG, font=("Segoe UI", 8), pady=(3, 6))

        plan = tk.Frame(body, bg=BG)
        plan.pack(fill="x", pady=(3, 0))
        self._mini_plan(plan, "Early", self.early_var, 0)
        self._mini_plan(plan, "Mid", self.mid_var, 1)
        self._mini_plan(plan, "Late", self.late_var, 2)

        self.window = window

    def _label(
        self,
        parent: tk.Widget,
        variable: tk.StringVar,
        fg: str,
        bg: str,
        font: tuple[str, int] | tuple[str, int, str],
        pady: tuple[int, int] | int = 0,
    ) -> tk.Label:
        label = tk.Label(
            parent,
            textvariable=variable,
            justify="left",
            anchor="w",
            wraplength=390,
            bg=bg,
            fg=fg,
            font=font,
        )
        label.pack(fill="x", pady=pady)
        return label

    def _section(self, parent: tk.Widget, title: str, variable: tk.StringVar, accent: str) -> None:
        row = tk.Frame(parent, bg=SURFACE_SOFT, highlightbackground="#242b35", highlightthickness=1)
        row.pack(fill="x", pady=(0, 5))
        marker = tk.Frame(row, width=3, bg=accent)
        marker.pack(side="left", fill="y")
        title_label = tk.Label(
            row,
            text=title.upper(),
            bg=SURFACE_SOFT,
            fg=accent,
            width=9,
            anchor="w",
            padx=8,
            pady=6,
            font=("Segoe UI", 8, "bold"),
        )
        title_label.pack(side="left")
        value = tk.Label(
            row,
            textvariable=variable,
            bg=SURFACE_SOFT,
            fg=TEXT,
            justify="left",
            anchor="w",
            wraplength=276,
            pady=6,
            font=("Segoe UI", 9),
        )
        value.pack(side="left", fill="x", expand=True, padx=(0, 8))

    def _mini_plan(self, parent: tk.Widget, title: str, variable: tk.StringVar, col: int) -> None:
        box = tk.Frame(parent, bg=SURFACE, highlightbackground="#242b35", highlightthickness=1)
        box.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 5, 0))
        parent.grid_columnconfigure(col, weight=1, uniform="plan")
        tk.Label(
            box,
            text=title,
            bg=SURFACE,
            fg=GOLD if title == "Late" else TEAL,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=7, pady=(5, 0))
        tk.Label(
            box,
            textvariable=variable,
            bg=SURFACE,
            fg=TEXT,
            justify="left",
            anchor="nw",
            wraplength=116,
            font=("Segoe UI", 8),
        ).pack(fill="both", expand=True, padx=7, pady=(1, 6))

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_start = (event.x, event.y)

    def _drag(self, event: tk.Event) -> None:
        if self.window is None or self._drag_start is None:
            return
        x = self.window.winfo_x() + event.x - self._drag_start[0]
        y = self.window.winfo_y() + event.y - self._drag_start[1]
        self.window.geometry(f"+{x}+{y}")

    def hide(self) -> None:
        if self.window is not None:
            self.window.withdraw()

    def update_text(self, text: str) -> None:
        parsed = _parse_overlay_text(text)
        self.status_var.set(parsed.get("status", "live"))
        self.comp_var.set(parsed.get("comp", "Aguardando leitura..."))
        self.shop_var.set(parsed.get("shop", "Loja: aguardando"))
        self.action_var.set(parsed.get("action", "Agora: aguardando estado do jogo"))
        self.economy_var.set(parsed.get("economy", "Economia: aguardando gold/level"))
        self.augment_var.set(parsed.get("augments", "Augments: sem tela de augment"))
        self.reason_var.set(parsed.get("reason", ""))
        self.early_var.set(parsed.get("early", "Early: -"))
        self.mid_var.set(parsed.get("mid", "Mid: -"))
        self.late_var.set(parsed.get("late", "Late: -"))


def _parse_overlay_text(text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    fallback: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if line.startswith("TFT AI Coach"):
            parsed["status"] = line.split("|", 1)[1].strip() if "|" in line else "live"
        elif lower.startswith("comp:"):
            parsed["comp"] = _wrap(line, 52)
        elif lower.startswith("loja:"):
            parsed["shop"] = _format_shop(line[5:].strip())
        elif lower.startswith("economia:"):
            parsed["economy"] = _wrap(line[9:].strip(), 56)
        elif lower.startswith("augments:"):
            parsed["augments"] = _wrap(line[9:].strip(), 56)
        elif lower.startswith("agora:"):
            parsed["action"] = _wrap(line[6:].strip(), 56)
        elif lower.startswith("por que:"):
            parsed["reason"] = _wrap(line, 72)
        elif lower.startswith("early:"):
            parsed["early"] = _wrap(line[6:].strip(), 30)
        elif lower.startswith("mid:"):
            parsed["mid"] = _wrap(line[4:].strip(), 30)
        elif lower.startswith("late:"):
            parsed["late"] = _wrap(line[5:].strip(), 34)
        else:
            fallback.append(line)
    if "comp" not in parsed and fallback:
        parsed["comp"] = _wrap(fallback[0], 52)
    return parsed


def _wrap(value: str, width: int) -> str:
    return "\n".join(textwrap.wrap(value, width=width, break_long_words=False)) or "-"


def _format_shop(value: str) -> str:
    names = [name.strip() for name in value.split(",") if name.strip()]
    if not names:
        return "aguardando loja"
    compact = [_compact_name(name) for name in names[:5]]
    line = "  |  ".join(compact)
    if len(line) <= 58:
        return line
    return "  |  ".join(compact[:3]) + "\n" + "  |  ".join(compact[3:])


def _compact_name(name: str) -> str:
    aliases = {
        "Aurelion Sol": "A. Sol",
        "Twisted Fate": "TF",
        "Miss Fortune": "MF",
        "Nunu & Willump": "Nunu",
        "Tahm Kench": "Tahm",
    }
    if name in aliases:
        return aliases[name]
    if len(name) <= 12:
        return name
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {' '.join(parts[1:])}"
    return name[:12]
