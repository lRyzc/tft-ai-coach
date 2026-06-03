from __future__ import annotations

import ctypes
import textwrap
import tkinter as tk

from tft_ai_coach.advisor.choices import best_decision_option
from tft_ai_coach.models import DecisionOption, GameState, Recommendation
from tft_ai_coach.ui.settings import load_overlay_settings, save_overlay_settings

BG = "#101318"
SURFACE = "#171b22"
SURFACE_SOFT = "#1d232b"
TEXT = "#f4f1e8"
MUTED = "#9da7b3"
GOLD = "#d8b34a"
BRIGHT_GOLD = "#ffd35a"
TEAL = "#62c7b4"
BRIGHT_TEAL = "#5ff0dc"
LINE = "#2b3340"
WARN = "#e6a04a"
TRANSPARENT = "#ff00ff"

GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
WS_EX_TOOLWINDOW = 0x00000080


class CoachOverlay:
    def __init__(self, parent: tk.Tk) -> None:
        self.parent = parent
        self.settings = load_overlay_settings()
        self.window: tk.Toplevel | None = None
        self.guide_window: tk.Toplevel | None = None
        self.guide_canvas: tk.Canvas | None = None
        self._drag_start: tuple[int, int] | None = None
        self.status_var = tk.StringVar(value="live")
        self.comp_var = tk.StringVar(value="Aguardando leitura...")
        self.shop_var = tk.StringVar(value="Loja: aguardando")
        self.action_var = tk.StringVar(value="Agora: aguardando estado do jogo")
        self.economy_var = tk.StringVar(value="Economia: aguardando gold/level")
        self.augment_var = tk.StringVar(value="sem escolha especial na tela")
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
        x = self.settings.compact_x if self.settings.compact_x is not None else max(20, screen_width - 452)
        y = self.settings.compact_y if self.settings.compact_y is not None else 78
        window.geometry(f"424x318+{x}+{y}")
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
        self._section(body, "Escolha", self.augment_var, accent=TEAL)
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
        self.settings.compact_x = x
        self.settings.compact_y = y
        save_overlay_settings(self.settings)

    def hide(self) -> None:
        if self.window is not None:
            self.window.withdraw()

    def hide_guides(self) -> None:
        if self.guide_window is not None:
            self.guide_window.withdraw()

    def set_choice_aura_enabled(self, enabled: bool) -> None:
        self.settings.show_choice_aura = enabled
        save_overlay_settings(self.settings)
        if not enabled:
            self.hide_guides()

    def choice_aura_enabled(self) -> bool:
        return self.settings.show_choice_aura

    def update_text(self, text: str) -> None:
        parsed = _parse_overlay_text(text)
        self.status_var.set(parsed.get("status", "live"))
        self.comp_var.set(parsed.get("comp", "Aguardando leitura..."))
        self.shop_var.set(parsed.get("shop", "Loja: aguardando"))
        self.action_var.set(parsed.get("action", "Agora: aguardando estado do jogo"))
        self.economy_var.set(parsed.get("economy", "Economia: aguardando gold/level"))
        self.augment_var.set(parsed.get("augments", "sem escolha especial na tela"))
        self.reason_var.set(parsed.get("reason", ""))
        self.early_var.set(parsed.get("early", "Early: -"))
        self.mid_var.set(parsed.get("mid", "Mid: -"))
        self.late_var.set(parsed.get("late", "Late: -"))

    def update_guides(
        self,
        state: GameState,
        recommendations: list[Recommendation],
        game_rect: tuple[int, int, int, int] | None,
    ) -> None:
        if not self.settings.show_choice_aura or game_rect is None:
            self.hide_guides()
            return
        option, reason = best_decision_option(state, recommendations)
        if option is None:
            self.hide_guides()
            return
        self._show_guide_window(game_rect)
        self._draw_choice_aura(option, reason, game_rect)

    def _show_guide_window(self, game_rect: tuple[int, int, int, int]) -> None:
        left, top, right, bottom = game_rect
        width = max(1, right - left)
        height = max(1, bottom - top)
        if self.guide_window is None:
            window = tk.Toplevel(self.parent)
            window.title("TFT Coach Guide")
            window.overrideredirect(True)
            window.attributes("-topmost", True)
            try:
                window.attributes("-transparentcolor", TRANSPARENT)
            except tk.TclError:
                window.attributes("-alpha", 0.34)
            window.configure(bg=TRANSPARENT)
            canvas = tk.Canvas(window, bg=TRANSPARENT, highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            self.guide_window = window
            self.guide_canvas = canvas
            window.update_idletasks()
            _make_clickthrough(window)
        self.guide_window.geometry(f"{width}x{height}+{left}+{top}")
        self.guide_window.deiconify()
        self.guide_window.lift()
        _make_clickthrough(self.guide_window)

    def _draw_choice_aura(
        self,
        option: DecisionOption,
        reason: str,
        game_rect: tuple[int, int, int, int],
    ) -> None:
        if self.guide_canvas is None:
            return
        left, top, right, bottom = game_rect
        width = max(1, right - left)
        height = max(1, bottom - top)
        self.guide_canvas.configure(width=width, height=height)
        self.guide_canvas.delete("all")
        x, y, w, h = _scale_region(option.region, width, height)
        x = max(2, x)
        y = max(2, y)
        w = min(w, width - x - 2)
        h = min(h, height - y - 2)
        title = _guide_title(option)
        detail = _short_reason(reason)
        accent = BRIGHT_GOLD if option.kind != "augment" else BRIGHT_TEAL

        for offset, color, stroke in [(10, "#7b5a19", 2), (6, accent, 3), (1, "#fff1a8", 2)]:
            self.guide_canvas.create_rectangle(
                x - offset,
                y - offset,
                x + w + offset,
                y + h + offset,
                outline=color,
                width=stroke,
            )
        self.guide_canvas.create_line(x, y - 18, x + w, y - 18, fill=accent, width=3)

        label_x = x + w / 2
        label_y = max(24, y - 48)
        label_width = min(360, max(220, w + 80))
        self.guide_canvas.create_rectangle(
            label_x - label_width / 2,
            label_y - 22,
            label_x + label_width / 2,
            label_y + 26,
            fill="#101318",
            outline=accent,
            width=2,
        )
        self.guide_canvas.create_text(
            label_x,
            label_y - 8,
            text=title,
            fill=accent,
            font=("Segoe UI", 12, "bold"),
        )
        self.guide_canvas.create_text(
            label_x,
            label_y + 11,
            text=detail,
            fill=TEXT,
            font=("Segoe UI", 9),
            width=label_width - 22,
        )


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
        elif lower.startswith("escolha:"):
            parsed["augments"] = _wrap(line[8:].strip(), 56)
        elif lower.startswith("divindade:"):
            parsed["augments"] = _wrap(line, 56)
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


def _scale_region(region: tuple[float, float, float, float], width: int, height: int) -> tuple[int, int, int, int]:
    x, y, w, h = region
    return int(x * width), int(y * height), int(w * width), int(h * height)


def _guide_title(option: DecisionOption) -> str:
    if option.kind == "divinity":
        return f"MELHOR DIVINDADE: {option.name}"
    if option.kind == "augment":
        return f"MELHOR AUGMENT: {option.name}"
    if option.kind == "reward":
        return f"MELHOR ESCOLHA: {option.name}"
    return f"MELHOR: {option.name}"


def _short_reason(reason: str) -> str:
    if ":" in reason:
        reason = reason.split(":", 1)[1].strip()
    return textwrap.shorten(reason, width=78, placeholder="...")


def _make_clickthrough(window: tk.Toplevel) -> None:
    try:
        hwnd = window.winfo_id()
        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW,
        )
    except Exception:
        return
