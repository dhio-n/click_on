import ctypes
import sys
import time
from ctypes import wintypes

from app.features.scanner.domain.scan_item import PopupDismissMode

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

VK_BACK = 0x08
VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_A = 0x41
VK_V = 0x56
VK_F8 = 0x77
VK_F9 = 0x78
VK_F10 = 0x79
KEYEVENTF_KEYUP = 0x0002


class Win32InputGateway:
    """Adapter Win32 API via ctypes para área de transferência, atalhos e simulação de teclas."""

    def __init__(self) -> None:
        self._is_windows = sys.platform == "win32"
        if self._is_windows:
            self._user32 = ctypes.windll.user32
            self._kernel32 = ctypes.windll.kernel32
            self._configure_win32_signatures()

    def _configure_win32_signatures(self) -> None:
        self._user32.OpenClipboard.argtypes = [wintypes.HWND]
        self._user32.OpenClipboard.restype = wintypes.BOOL
        self._user32.EmptyClipboard.argtypes = []
        self._user32.EmptyClipboard.restype = wintypes.BOOL
        self._user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        self._user32.SetClipboardData.restype = wintypes.HANDLE
        self._user32.CloseClipboard.argtypes = []
        self._user32.CloseClipboard.restype = wintypes.BOOL

        self._kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        self._kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        self._kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        self._kernel32.GlobalLock.restype = wintypes.LPVOID
        self._kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        self._kernel32.GlobalUnlock.restype = wintypes.BOOL

    def set_clipboard(self, text: str) -> bool:
        """Copia texto para a área de transferência do Windows de forma segura."""
        if not self._is_windows:
            return True

        for _ in range(10):
            if self._user32.OpenClipboard(None):
                try:
                    self._user32.EmptyClipboard()
                    raw_bytes = text.encode("utf-16le") + b"\x00\x00"
                    h_mem = self._kernel32.GlobalAlloc(GMEM_MOVEABLE, len(raw_bytes))
                    p_mem = self._kernel32.GlobalLock(h_mem)
                    ctypes.memmove(p_mem, raw_bytes, len(raw_bytes))
                    self._kernel32.GlobalUnlock(h_mem)
                    self._user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                    return True
                finally:
                    self._user32.CloseClipboard()
            time.sleep(0.02)
        return False

    def press_key(self, vk: int, delay_after: float = 0.04) -> None:
        if not self._is_windows:
            return
        self._user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.02)
        self._user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        if delay_after > 0:
            time.sleep(delay_after)

    def press_ctrl_combo(self, vk: int, delay_after: float = 0.04) -> None:
        if not self._is_windows:
            return
        self._user32.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.02)
        self._user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.03)
        self._user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        self._user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        if delay_after > 0:
            time.sleep(delay_after)

    def dismiss_popup(self, mode: PopupDismissMode) -> None:
        if mode == PopupDismissMode.ESC_ENTER:
            self.press_key(VK_ESCAPE, delay_after=0.06)
            self.press_key(VK_RETURN, delay_after=0.08)
        elif mode == PopupDismissMode.ESC_ONLY:
            self.press_key(VK_ESCAPE, delay_after=0.08)
        elif mode == PopupDismissMode.ENTER_ONLY:
            self.press_key(VK_RETURN, delay_after=0.08)
        elif mode == PopupDismissMode.SPACE:
            self.press_key(VK_SPACE, delay_after=0.08)

    def clean_input_bar(self) -> None:
        self.press_ctrl_combo(VK_A, delay_after=0.04)
        self.press_key(VK_BACK, delay_after=0.05)

    def send_code(
        self,
        *,
        code: str,
        clean_before: bool,
        dismiss_mode: PopupDismissMode | None,
    ) -> bool:
        if dismiss_mode is not None:
            self.dismiss_popup(dismiss_mode)
            time.sleep(0.04)

        if clean_before:
            self.clean_input_bar()
            time.sleep(0.04)

        copied = self.set_clipboard(code)
        time.sleep(0.04)
        self.press_ctrl_combo(VK_V, delay_after=0.06)
        self.press_key(VK_RETURN, delay_after=0.05)
        return copied

    def dismiss_and_clean(self, *, dismiss_mode: PopupDismissMode) -> None:
        self.dismiss_popup(dismiss_mode)
        time.sleep(0.05)
        self.clean_input_bar()

    def beep(self, *, frequency: int, duration_ms: int) -> None:
        if not self._is_windows:
            return
        try:
            self._kernel32.Beep(frequency, duration_ms)
        except Exception:
            return

    def is_key_pressed(self, vk: int) -> bool:
        if not self._is_windows:
            return False
        try:
            return bool(self._user32.GetAsyncKeyState(vk) & 0x8000)
        except Exception:
            return False
