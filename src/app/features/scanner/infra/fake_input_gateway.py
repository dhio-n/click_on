from dataclasses import dataclass

from app.features.scanner.domain.scan_item import PopupDismissMode


@dataclass(frozen=True, slots=True)
class SentCodeRecord:
    code: str
    clean_before: bool
    dismiss_mode: PopupDismissMode | None


class FakeInputGateway:
    """Fake em memória para testar automação de envio sem acionar Win32 API real."""

    def __init__(self, *, clipboard_succeeds: bool = True) -> None:
        self.clipboard_succeeds = clipboard_succeeds
        self.sent_codes: list[SentCodeRecord] = []
        self.dismiss_calls: list[PopupDismissMode] = []
        self.beeps: list[tuple[int, int]] = []

    def send_code(
        self,
        *,
        code: str,
        clean_before: bool,
        dismiss_mode: PopupDismissMode | None,
    ) -> bool:
        self.sent_codes.append(
            SentCodeRecord(code=code, clean_before=clean_before, dismiss_mode=dismiss_mode)
        )
        return self.clipboard_succeeds

    def dismiss_and_clean(self, *, dismiss_mode: PopupDismissMode) -> None:
        self.dismiss_calls.append(dismiss_mode)

    def beep(self, *, frequency: int, duration_ms: int) -> None:
        self.beeps.append((frequency, duration_ms))
