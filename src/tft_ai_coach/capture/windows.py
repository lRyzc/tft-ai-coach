from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import numpy as np

try:
    import win32con
    import win32gui
    import win32ui
except Exception:  # pragma: no cover - only happens off Windows or without pywin32
    win32con = None
    win32gui = None
    win32ui = None


@dataclass(slots=True)
class WindowInfo:
    hwnd: int
    title: str
    rect: tuple[int, int, int, int]


@dataclass(slots=True)
class CapturedFrame:
    image: np.ndarray
    title: str
    rect: tuple[int, int, int, int]
    captured_at: datetime


def list_windows() -> list[WindowInfo]:
    if win32gui is None:
        return []
    windows: list[WindowInfo] = []

    def enum_handler(hwnd: int, _: object) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd).strip()
        if not title:
            return
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        if width < 200 or height < 120:
            return
        windows.append(WindowInfo(hwnd=hwnd, title=title, rect=rect))

    win32gui.EnumWindows(enum_handler, None)
    return sorted(windows, key=lambda item: item.title.lower())


def find_window(title_hint: str) -> WindowInfo | None:
    hint = title_hint.lower()
    for window in list_windows():
        if hint in window.title.lower():
            return window
    return None


class WindowCapture:
    def capture(self, title_hint: str) -> CapturedFrame:
        window = find_window(title_hint)
        if window is None:
            raise RuntimeError(f"Window not found: {title_hint}")
        return self.capture_hwnd(window.hwnd, window.title)

    def capture_hwnd(self, hwnd: int, title: str = "") -> CapturedFrame:
        if win32gui is None or win32ui is None or win32con is None:
            raise RuntimeError("pywin32 is required for window capture on Windows")

        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            raise RuntimeError("Window has no capturable area")

        window_dc = win32gui.GetWindowDC(hwnd)
        source_dc = win32ui.CreateDCFromHandle(window_dc)
        memory_dc = source_dc.CreateCompatibleDC()
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(source_dc, width, height)
        memory_dc.SelectObject(bitmap)
        memory_dc.BitBlt((0, 0), (width, height), source_dc, (0, 0), win32con.SRCCOPY)

        raw = bitmap.GetBitmapBits(True)
        image = np.frombuffer(raw, dtype=np.uint8)
        image.shape = (height, width, 4)
        image = image[..., :3]
        image = np.ascontiguousarray(image)

        source_dc.DeleteDC()
        memory_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, window_dc)
        win32gui.DeleteObject(bitmap.GetHandle())

        return CapturedFrame(image=image, title=title, rect=(left, top, right, bottom), captured_at=datetime.now())


def titles(windows: Iterable[WindowInfo]) -> list[str]:
    return [window.title for window in windows]

