from __future__ import annotations

import json
import time
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
from PIL import Image, ImageOps, ImageTk

from tft_ai_coach.advisor import CoachEngine, compact_overlay_summary
from tft_ai_coach.capture import WindowCapture, list_windows
from tft_ai_coach.data.ddragon import load_current_index, update_static_data
from tft_ai_coach.data.meta import load_comps
from tft_ai_coach.models import CompDefinition, GameState, Recommendation
from tft_ai_coach.paths import DDRAGON_DIR, SCREENSHOT_DIR, ensure_dirs
from tft_ai_coach.ui.overlay import CoachOverlay
from tft_ai_coach.vision import VisionPipeline

APP_BG = "#0f1117"
PANEL_BG = "#151a22"
CARD_BG = "#1c2230"
CARD_SOFT = "#22293a"
LINE = "#30384a"
TEXT = "#f7f3e8"
MUTED = "#a8b0bf"
GOLD = "#f0bd3d"
TEAL = "#59d0c4"
GREEN = "#5fd17a"
RED = "#e46b6b"


class CoachApp:
    def __init__(self) -> None:
        ensure_dirs()
        self.root = tk.Tk()
        self.root.title("TFT AI Coach")
        self.root.geometry("1120x720")
        self.root.minsize(980, 620)

        self.capture = WindowCapture()
        self.vision = VisionPipeline()
        self.overlay = CoachOverlay(self.root)
        self.index = load_current_index()
        self.comps = load_comps()
        self.engine = CoachEngine(self.comps)
        self.last_state = GameState()
        self.window_titles: list[str] = []
        self.live_running = False
        self.live_after_id: str | None = None
        self.live_interval_ms = 1800
        self._image_cache: dict[str, ImageTk.PhotoImage] = {}

        self._build()
        self.refresh_windows()
        self.refresh_data_status()

    def run(self) -> None:
        self.root.mainloop()

    def _build(self) -> None:
        self.root.configure(bg=APP_BG)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=APP_BG)
        style.configure("TLabel", background=APP_BG, foreground=TEXT)
        style.configure("TButton", padding=7)
        style.configure("TNotebook", background=APP_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL_BG, foreground=MUTED, padding=(14, 8))
        style.map("TNotebook.Tab", background=[("selected", CARD_BG)], foreground=[("selected", TEXT)])
        style.configure("TCombobox", fieldbackground="#f4f6f8")

        shell = ttk.Frame(self.root, padding=16)
        shell.pack(fill="both", expand=True)

        header = tk.Frame(shell, bg=APP_BG)
        header.pack(fill="x")
        tk.Label(header, text="TFT AI Coach", bg=APP_BG, fg=TEXT, font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(header, text="Meta, leitura de tela e overlay pessoal", bg=APP_BG, fg=MUTED, font=("Segoe UI", 10)).pack(
            side="left", padx=(12, 0), pady=(10, 0)
        )
        self.data_status = tk.Label(header, text="", bg=APP_BG, fg=GOLD, font=("Segoe UI", 9, "bold"))
        self.data_status.pack(side="right", pady=(8, 0))

        controls = tk.Frame(shell, bg=APP_BG)
        controls.pack(fill="x", pady=(14, 10))
        self._command_button(controls, "Atualizar dados", self.update_data).pack(side="left", padx=(0, 8))
        self._command_button(controls, "Listar janelas", self.refresh_windows).pack(side="left", padx=(0, 8))
        self._command_button(controls, "Capturar uma vez", self.capture_once).pack(side="left", padx=(0, 8))
        self._command_button(controls, "Gerar recomendacao", self.recommend_from_form).pack(side="left", padx=(0, 8))
        self._command_button(controls, "Overlay", self.toggle_overlay).pack(side="left")
        self.live_button = self._command_button(controls, "Iniciar Live Coach", self.toggle_live, primary=True)
        self.live_button.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Pronto.")
        tk.Label(shell, textvariable=self.status_var, bg=APP_BG, fg=MUTED, anchor="w", font=("Segoe UI", 9)).pack(
            fill="x", pady=(0, 8)
        )

        window_row = tk.Frame(shell, bg=APP_BG)
        window_row.pack(fill="x", pady=(0, 12))
        tk.Label(window_row, text="Janela do TFT:", bg=APP_BG, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
        self.window_var = tk.StringVar()
        self.window_combo = ttk.Combobox(window_row, textvariable=self.window_var, values=[], width=80)
        self.window_combo.pack(side="left", padx=(8, 0), fill="x", expand=True)

        notebook = ttk.Notebook(shell)
        notebook.pack(fill="both", expand=True)

        meta_tab = tk.Frame(notebook, bg=APP_BG)
        live_tab = tk.Frame(notebook, bg=APP_BG)
        notebook.add(meta_tab, text="Meta comps")
        notebook.add(live_tab, text="Leitura ao vivo")

        self._build_meta_panel(meta_tab)

        paned = ttk.PanedWindow(live_tab, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=2, pady=12)

        left = ttk.Frame(paned, padding=10)
        right = ttk.Frame(paned, padding=10)
        paned.add(left, weight=1)
        paned.add(right, weight=1)

        self._build_state_form(left)
        self._build_results(right)

    def _command_button(self, parent: tk.Widget, text: str, command, primary: bool = False) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=GOLD if primary else CARD_SOFT,
            fg="#17130a" if primary else TEXT,
            activebackground="#ffd15d" if primary else "#2c3549",
            activeforeground="#17130a" if primary else TEXT,
            relief="flat",
            borderwidth=0,
            padx=12,
            pady=8,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )

    def _build_meta_panel(self, parent: tk.Frame) -> None:
        top = tk.Frame(parent, bg=APP_BG)
        top.pack(fill="x", pady=(12, 10))
        copy = tk.Frame(top, bg=APP_BG)
        copy.pack(side="left", fill="x", expand=True)
        tk.Label(copy, text="Comps do meta", bg=APP_BG, fg=TEXT, font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(
            copy,
            text="Tier, dificuldade, ritmo e unidades chave para estudar antes e durante a partida.",
            bg=APP_BG,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(3, 0))

        live_box = tk.Frame(top, bg=PANEL_BG, highlightbackground=LINE, highlightthickness=1, padx=12, pady=8)
        live_box.pack(side="right", padx=(14, 0))
        tk.Label(live_box, text="Live Coach", bg=PANEL_BG, fg=TEAL, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(
            live_box,
            text="Vendo loja, gold, stage, augments e divindade.",
            bg=PANEL_BG,
            fg=TEXT,
            font=("Segoe UI", 9),
            wraplength=250,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(parent, bg=APP_BG)
        body.pack(fill="both", expand=True)

        canvas = tk.Canvas(body, bg=APP_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        cards = tk.Frame(canvas, bg=APP_BG)
        window_id = canvas.create_window((0, 0), window=cards, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def resize_cards(event: tk.Event) -> None:
            canvas.itemconfigure(window_id, width=event.width)

        def update_scroll(_event: tk.Event) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", resize_cards)
        cards.bind("<Configure>", update_scroll)
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

        for comp in sorted(self.comps, key=_comp_sort_key):
            self._comp_card(cards, comp)

    def _comp_card(self, parent: tk.Frame, comp: CompDefinition) -> None:
        card = tk.Frame(parent, bg=CARD_BG, highlightbackground=LINE, highlightthickness=1)
        card.pack(fill="x", pady=6, padx=(0, 10))

        left = tk.Frame(card, bg=CARD_BG, padx=14, pady=12)
        left.pack(side="left", fill="y")
        tk.Label(left, text=comp.name, bg=CARD_BG, fg=TEXT, font=("Segoe UI", 12, "bold"), width=20, anchor="w").pack(
            anchor="w"
        )
        badge_row = tk.Frame(left, bg=CARD_BG)
        badge_row.pack(anchor="w", pady=(8, 0))
        self._badge(badge_row, comp.stats.get("patch", self.index.get("set_id", "?")), fg=TEXT, bg="#101422").pack(
            side="left", padx=(0, 5)
        )
        self._badge(badge_row, comp.tempo or comp.style, fg=TEXT, bg="#111827").pack(side="left", padx=(0, 5))
        self._badge(badge_row, comp.difficulty, fg=_difficulty_color(comp.difficulty), bg="#121722").pack(side="left")

        tier = tk.Frame(card, bg=CARD_BG, padx=6, pady=12)
        tier.pack(side="left", fill="y")
        tk.Label(
            tier,
            text=comp.tier.upper(),
            bg="#231f12",
            fg=GOLD,
            width=3,
            height=2,
            font=("Segoe UI", 13, "bold"),
            highlightbackground=GOLD,
            highlightthickness=1,
        ).pack(anchor="center")

        units = tk.Frame(card, bg=CARD_BG, padx=6, pady=10)
        units.pack(side="left", fill="x", expand=True)
        for unit in (comp.carry_units + [name for name in comp.core_units if name not in comp.carry_units])[:9]:
            self._unit_avatar(units, unit, carry=unit in comp.carry_units).pack(side="left", padx=5)

        right = tk.Frame(card, bg=CARD_SOFT, width=104)
        right.pack(side="right", fill="y")
        tk.Label(right, text="CARRIES", bg=CARD_SOFT, fg=MUTED, font=("Segoe UI", 7, "bold")).pack(pady=(14, 2))
        carry_text = ", ".join(comp.carry_units[:2]) or "Flex"
        tk.Label(right, text=carry_text, bg=CARD_SOFT, fg=TEXT, font=("Segoe UI", 8), wraplength=86).pack()
        tk.Button(
            right,
            text="Focar",
            command=lambda item=comp: self._focus_comp(item),
            bg=GOLD,
            fg="#17130a",
            activebackground="#ffd15d",
            activeforeground="#17130a",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=5,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
        ).pack(pady=(12, 12))

    def _badge(self, parent: tk.Widget, text: str, fg: str, bg: str) -> tk.Label:
        return tk.Label(parent, text=text, bg=bg, fg=fg, padx=7, pady=2, font=("Segoe UI", 8, "bold"))

    def _unit_avatar(self, parent: tk.Widget, name: str, carry: bool = False) -> tk.Frame:
        box = tk.Frame(parent, bg=CARD_BG)
        photo = self._champion_photo(name, 46)
        border = GOLD if carry else "#454d61"
        icon_frame = tk.Frame(box, bg=border, padx=2, pady=2)
        icon_frame.pack()
        if photo is not None:
            tk.Label(icon_frame, image=photo, bg=border).pack()
        else:
            tk.Label(icon_frame, text=name[:2].upper(), bg="#111827", fg=TEXT, width=6, height=3).pack()
        label = _short_name(name)
        tk.Label(box, text=label, bg=CARD_BG, fg=TEXT, font=("Segoe UI", 8), width=9).pack(pady=(4, 0))
        return box

    def _champion_photo(self, champion_name: str, size: int) -> ImageTk.PhotoImage | None:
        record = self._champion_record(champion_name)
        if record is None:
            return None
        path = DDRAGON_DIR / self.index["version"] / "icons" / record["image_group"] / record["image_file"]
        if not path.exists():
            return None
        key = f"{path}:{size}"
        if key not in self._image_cache:
            image = Image.open(path).convert("RGB")
            image = ImageOps.fit(image, (size, size), method=Image.Resampling.LANCZOS)
            self._image_cache[key] = ImageTk.PhotoImage(image)
        return self._image_cache[key]

    def _champion_record(self, champion_name: str) -> dict | None:
        target = _norm_name(champion_name)
        for record in self.index.get("records", {}).get("champions", []):
            if _norm_name(record["name"]) == target:
                return record
        return None

    def _focus_comp(self, comp: CompDefinition) -> None:
        self.overlay.show()
        lines = [
            "TFT AI Coach | foco",
            f"Comp: {comp.name} ({comp.tier})",
            f"Loja: {', '.join(comp.early_units[:5] or comp.core_units[:5])}",
            f"Escolha: priorize augments de {', '.join(comp.augment_keywords[:3]) or comp.style}",
            f"Agora: siga {comp.tempo or comp.style}; carries: {', '.join(comp.carry_units[:3]) or 'flex'}",
            f"Early: {', '.join(comp.early_units[:4]) or '-'}",
            f"Mid: {', '.join(comp.mid_units[:4]) or '-'}",
            f"Late: {', '.join(comp.core_units[:5]) or '-'}",
        ]
        self.overlay.update_text("\n".join(lines))
        self.status_var.set(f"Foco definido no overlay: {comp.name}.")

    def _build_state_form(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Estado do jogo", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        form = ttk.Frame(parent)
        form.pack(fill="x", pady=(10, 8))

        self.stage_var = tk.StringVar()
        self.level_var = tk.StringVar()
        self.gold_var = tk.StringVar()

        for idx, (label, var) in enumerate([("Stage", self.stage_var), ("Level", self.level_var), ("Gold", self.gold_var)]):
            ttk.Label(form, text=label).grid(row=0, column=idx * 2, sticky="w", padx=(0, 6))
            ttk.Entry(form, textvariable=var, width=10).grid(row=0, column=idx * 2 + 1, sticky="ew", padx=(0, 12))

        self.board_text = self._text_area(parent, "Board", height=4)
        self.bench_text = self._text_area(parent, "Banco", height=3)
        self.shop_text = self._text_area(parent, "Loja", height=3)
        self.items_text = self._text_area(parent, "Itens/componentes", height=3)
        self.augments_text = self._text_area(parent, "Augments", height=3)

        hint = "Use virgulas ou linhas novas. Ex: Ezreal, Leona, Xayah"
        ttk.Label(parent, text=hint, foreground="#555b66").pack(anchor="w", pady=(4, 0))

    def _build_results(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Coach", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.recommendation_text = tk.Text(parent, height=18, wrap="word", borderwidth=1, relief="solid")
        self.recommendation_text.pack(fill="both", expand=True, pady=(10, 10))

        ttk.Label(parent, text="Debug da captura/visao", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.debug_text = tk.Text(parent, height=10, wrap="word", borderwidth=1, relief="solid")
        self.debug_text.pack(fill="both", expand=True, pady=(8, 0))

    def _text_area(self, parent: ttk.Frame, label: str, height: int) -> tk.Text:
        ttk.Label(parent, text=label).pack(anchor="w", pady=(8, 3))
        text = tk.Text(parent, height=height, wrap="word", borderwidth=1, relief="solid")
        text.pack(fill="x")
        return text

    def refresh_data_status(self) -> None:
        self.data_status.configure(
            text=f"Patch {self.index.get('version', '?')} | Set {self.index.get('set_id', '?')}"
        )

    def update_data(self) -> None:
        try:
            self.index = update_static_data(download_icons=True)
            self.refresh_data_status()
            messagebox.showinfo("Dados atualizados", f"Patch {self.index['version']} baixado.")
        except Exception as exc:
            messagebox.showerror("Erro ao atualizar", str(exc))

    def refresh_windows(self) -> None:
        windows = list_windows()
        self.window_titles = [window.title for window in windows]
        self.window_combo.configure(values=self.window_titles)
        if self.window_titles and not self.window_var.get():
            preferred = next((title for title in self.window_titles if "league" in title.lower() or "teamfight" in title.lower()), self.window_titles[0])
            self.window_var.set(preferred)
        if self.window_titles:
            self.status_var.set(f"{len(self.window_titles)} janelas encontradas. Abra a lista e escolha League/TFT.")
            self._write_debug({"windows": [{"title": window.title, "rect": window.rect} for window in windows[:40]]})
        else:
            self.status_var.set("Nenhuma janela encontrada. Reabra o app e tente novamente.")
            self._write_debug({"windows": []})

    def capture_once(self) -> None:
        try:
            state, debug_payload = self._capture_and_analyze(hide_root=True, save_debug=True)
            self._populate_empty_fields(state, force=False)
            self.last_state = self._merge_manual_state(state)
            recommendations = self.engine.recommend(self.last_state)
            self._write_debug(debug_payload)
            self._render_recommendations(recommendations)
            self.overlay.update_text(compact_overlay_summary(self.last_state, recommendations))
            self.status_var.set("Captura feita. Veja a loja detectada e o debug.")
        except Exception as exc:
            messagebox.showerror("Erro na captura", str(exc))
            self.status_var.set(f"Erro na captura: {exc}")

    def toggle_live(self) -> None:
        if self.live_running:
            self.stop_live()
        else:
            self.start_live()

    def start_live(self) -> None:
        title = self.window_var.get().strip()
        if not title:
            self.refresh_windows()
            title = self.window_var.get().strip()
        if not title:
            messagebox.showwarning("Sem janela", "Escolha a janela do TFT primeiro.")
            return
        self.live_running = True
        self.live_button.configure(text="Parar Live Coach")
        self.overlay.show()
        self.status_var.set("Live Coach ligado. O overlay sera atualizado automaticamente.")
        self._live_tick()

    def stop_live(self) -> None:
        self.live_running = False
        self.live_button.configure(text="Iniciar Live Coach")
        if self.live_after_id is not None:
            self.root.after_cancel(self.live_after_id)
            self.live_after_id = None
        self.status_var.set("Live Coach parado.")

    def _live_tick(self) -> None:
        if not self.live_running:
            return
        try:
            state, debug_payload = self._capture_and_analyze(hide_root=False, save_debug=False)
            self._populate_empty_fields(state, force=True)
            self.last_state = self._merge_manual_state(state)
            recommendations = self.engine.recommend(self.last_state)
            self._render_recommendations(recommendations)
            self.overlay.update_text(compact_overlay_summary(self.last_state, recommendations))
            self._write_debug(debug_payload)
            self.status_var.set("Live Coach lendo a tela automaticamente.")
        except Exception as exc:
            self.status_var.set(f"Live Coach: {exc}")
            self.overlay.update_text(f"TFT AI Coach\nErro na leitura:\n{exc}")
        self.live_after_id = self.root.after(self.live_interval_ms, self._live_tick)

    def _capture_and_analyze(self, hide_root: bool, save_debug: bool) -> tuple[GameState, dict]:
        title = self.window_var.get().strip()
        if not title:
            raise RuntimeError("Escolha a janela do TFT primeiro.")
        if hide_root:
            self.root.withdraw()
            self.root.update_idletasks()
            time.sleep(0.2)
        try:
            frame = self.capture.capture(title)
        finally:
            if hide_root:
                self.root.deiconify()

        state = self.vision.analyze(frame.image)
        debug_payload = {
            "captured_window": frame.title,
            "rect": frame.rect,
            "vision": self.vision.debug,
        }
        if save_debug:
            path = SCREENSHOT_DIR / "latest_capture.png"
            cv2.imwrite(str(path), frame.image)
            crop_dir = SCREENSHOT_DIR / "latest_regions"
            crops = self.vision.export_debug_crops(frame.image, crop_dir)
            debug_payload.update(
                {
                    "saved_to": str(path),
                    "debug_crops": str(crop_dir),
                    "debug_crop_count": len(crops),
                }
            )
        return state, debug_payload

    def recommend_from_form(self) -> None:
        self.last_state = self._merge_manual_state(GameState())
        self._render_recommendations(self.engine.recommend(self.last_state))

    def toggle_overlay(self) -> None:
        self.overlay.show()
        self.overlay.update_text(self._overlay_text())

    def _merge_manual_state(self, base: GameState) -> GameState:
        manual_stage = self.stage_var.get().strip()
        manual_level = _optional_int(self.level_var.get())
        manual_gold = _optional_int(self.gold_var.get())
        manual_board = _split_entries(self.board_text.get("1.0", "end"))
        manual_bench = _split_entries(self.bench_text.get("1.0", "end"))
        manual_shop = _split_entries(self.shop_text.get("1.0", "end"))
        manual_items = _split_entries(self.items_text.get("1.0", "end"))
        manual_augments = _split_entries(self.augments_text.get("1.0", "end"))

        base.stage = manual_stage or base.stage
        base.level = manual_level if manual_level is not None else base.level
        base.gold = manual_gold if manual_gold is not None else base.gold
        base.board = manual_board or base.board
        base.bench = manual_bench or base.bench
        base.shop = manual_shop or base.shop
        base.items = manual_items or base.items
        base.augments = manual_augments or base.augments
        return base

    def _populate_empty_fields(self, state: GameState, force: bool = False) -> None:
        if state.stage and (force or not self.stage_var.get().strip()):
            self.stage_var.set(state.stage)
        if state.level is not None and (force or not self.level_var.get().strip()):
            self.level_var.set(str(state.level))
        if state.gold is not None and (force or not self.gold_var.get().strip()):
            self.gold_var.set(str(state.gold))
        if state.shop and (force or not _split_entries(self.shop_text.get("1.0", "end"))):
            self.shop_text.delete("1.0", "end")
            self.shop_text.insert("1.0", ", ".join(state.shop))
        if state.augments and (force or not _split_entries(self.augments_text.get("1.0", "end"))):
            self.augments_text.delete("1.0", "end")
            self.augments_text.insert("1.0", ", ".join(state.augments))

    def _render_recommendations(self, recommendations: list[Recommendation]) -> None:
        if not recommendations:
            output = "Ainda nao ha comps cadastradas em data/meta/comps.json."
        else:
            chunks: list[str] = []
            for index, rec in enumerate(recommendations, start=1):
                chunks.append(f"{index}. {rec.comp.name} ({rec.comp.tier}) - score {rec.score}")
                chunks.append("Por que:")
                chunks.extend(f"- {reason}" for reason in rec.reasons)
                chunks.append("Acoes:")
                chunks.extend(f"- {action}" for action in rec.actions[:5])
                chunks.append("")
            output = "\n".join(chunks).strip()

        self.recommendation_text.delete("1.0", "end")
        self.recommendation_text.insert("1.0", output)
        self.overlay.update_text(self._overlay_text())

    def _overlay_text(self) -> str:
        text = self.recommendation_text.get("1.0", "end").strip()
        if not text:
            return "Aguardando recomendacao..."
        lines = text.splitlines()
        return "\n".join(lines[:8])

    def _write_debug(self, payload: dict) -> None:
        self.debug_text.delete("1.0", "end")
        self.debug_text.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False))


def _split_entries(value: str) -> list[str]:
    normalized = value.replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _optional_int(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _comp_sort_key(comp: CompDefinition) -> tuple[int, str]:
    tier_rank = {"S": 0, "A": 1, "B": 2, "C": 3}.get(comp.tier.upper(), 4)
    return (tier_rank, comp.name)


def _difficulty_color(value: str) -> str:
    lower = value.lower()
    if "easy" in lower:
        return GREEN
    if "hard" in lower:
        return RED
    return GOLD


def _short_name(value: str) -> str:
    aliases = {
        "Aurelion Sol": "A. Sol",
        "Miss Fortune": "Miss F.",
        "The Mighty Mech": "Mech",
        "Blitzcrank": "Blitz",
        "Mordekaiser": "Morde",
        "Rammus": "Ramm.",
    }
    if value in aliases:
        return aliases[value]
    if len(value) <= 8:
        return value
    return value[:7] + "."


def _norm_name(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def main() -> None:
    CoachApp().run()


if __name__ == "__main__":
    main()
