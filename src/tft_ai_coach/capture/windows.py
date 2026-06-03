from __future__ import annotations

import ctypes
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import mss

import numpy as np

user32 = ctypes.windll.user32


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
    windows: list[WindowInfo] = []

    def enum_handler(hwnd: int, _: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        title_length = user32.GetWindowTextLengthW(hwnd)
        if title_length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(title_length + 1)
        user32.GetWindowTextW(hwnd, buffer, title_length + 1)
        title = buffer.value.strip()
        if not title:
            return True
        rect_struct = RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect_struct)):
            return True
        rect = (rect_struct.left, rect_struct.top, rect_struct.right, rect_struct.bottom)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        if width < 200 or height < 120:
            return True
        windows.append(WindowInfo(hwnd=hwnd, title=title, rect=rect))
        return True

    enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)(enum_handler)
    user32.EnumWindows(enum_proc, 0)
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
        rect_struct = RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect_struct)):
            raise RuntimeError("Could not read window rectangle")
        left, top, right, bottom = rect_struct.left, rect_struct.top, rect_struct.right, rect_struct.bottom
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            raise RuntimeError("Window has no capturable area")

        with mss.mss() as capture:
            raw = capture.grab({"left": left, "top": top, "width": width, "height": height})
            image = np.array(raw, dtype=np.uint8)[..., :3]
            image = np.ascontiguousarray(image)

        return CapturedFrame(image=image, title=title, rect=(left, top, right, bottom), captured_at=datetime.now())


def titles(windows: Iterable[WindowInfo]) -> list[str]:
    return [window.title for window in windows]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]
