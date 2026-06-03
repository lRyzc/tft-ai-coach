from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import cv2

from tft_ai_coach.advisor import CoachEngine
from tft_ai_coach.capture import WindowCapture, list_windows
from tft_ai_coach.data.ddragon import load_current_index, update_static_data
from tft_ai_coach.data.meta import load_comps
from tft_ai_coach.models import GameState, Recommendation
from tft_ai_coach.paths import SCREENSHOT_DIR, ensure_dirs
from tft_ai_coach.ui.overlay import CoachOverlay
from tft_ai_coach.vision import VisionPipeline


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
        self.engine = CoachEngine(load_comps())
        self.last_state = GameState()
        self.window_titles: list[str] = []

        self._build()
        self.refresh_windows()
        self.refresh_data_status()

    def run(self) -> None:
        self.root.mainloop()

    def _build(self) -> None:
        self.root.configure(bg="#f4f6f8")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f6f8")
        style.configure("TLabel", background="#f4f6f8", foreground="#1a1d24")
        style.configure("TButton", padding=7)

        shell = ttk.Frame(self.root, padding=16)
        shell.pack(fill="both", expand=True)

        header = ttk.Frame(shell)
        header.pack(fill="x")
        ttk.Label(header, text="TFT AI Coach", font=("Segoe UI", 18, "bold")).pack(side="left")
        self.data_status = ttk.Label(header, text="")
        self.data_status.pack(side="right")

        controls = ttk.Frame(shell)
        controls.pack(fill="x", pady=(14, 10))
        ttk.Button(controls, text="Atualizar dados TFT", command=self.update_data).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Listar janelas", command=self.refresh_windows).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Capturar uma vez", command=self.capture_once).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Gerar recomendacao", command=self.recommend_from_form).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Overlay", command=self.toggle_overlay).pack(side="left")

        window_row = ttk.Frame(shell)
        window_row.pack(fill="x", pady=(0, 12))
        ttk.Label(window_row, text="Janela do TFT:").pack(side="left")
        self.window_var = tk.StringVar()
        self.window_combo = ttk.Combobox(window_row, textvariable=self.window_var, values=[], width=80)
        self.window_combo.pack(side="left", padx=(8, 0), fill="x", expand=True)

        paned = ttk.PanedWindow(shell, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned, padding=10)
        right = ttk.Frame(paned, padding=10)
        paned.add(left, weight=1)
        paned.add(right, weight=1)

        self._build_state_form(left)
        self._build_results(right)

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

    def capture_once(self) -> None:
        title = self.window_var.get().strip()
        if not title:
            messagebox.showwarning("Sem janela", "Escolha uma janela primeiro.")
            return
        try:
            frame = self.capture.capture(title)
            state = self.vision.analyze(frame.image)
            self.last_state = self._merge_manual_state(state)
            path = SCREENSHOT_DIR / "latest_capture.png"
            cv2.imwrite(str(path), frame.image)
            self._write_debug(
                {
                    "captured_window": frame.title,
                    "rect": frame.rect,
                    "saved_to": str(path),
                    "vision": self.vision.debug,
                }
            )
            self._render_recommendations(self.engine.recommend(self.last_state))
        except Exception as exc:
            messagebox.showerror("Erro na captura", str(exc))

    def recommend_from_form(self) -> None:
        self.last_state = self._merge_manual_state(GameState())
        self._render_recommendations(self.engine.recommend(self.last_state))

    def toggle_overlay(self) -> None:
        self.overlay.show()
        self.overlay.update_text(self._overlay_text())

    def _merge_manual_state(self, base: GameState) -> GameState:
        base.stage = self.stage_var.get().strip()
        base.level = _optional_int(self.level_var.get())
        base.gold = _optional_int(self.gold_var.get())
        base.board = _split_entries(self.board_text.get("1.0", "end"))
        base.bench = _split_entries(self.bench_text.get("1.0", "end"))
        base.shop = _split_entries(self.shop_text.get("1.0", "end"))
        base.items = _split_entries(self.items_text.get("1.0", "end"))
        base.augments = _split_entries(self.augments_text.get("1.0", "end"))
        return base

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


def main() -> None:
    CoachApp().run()


if __name__ == "__main__":
    main()

