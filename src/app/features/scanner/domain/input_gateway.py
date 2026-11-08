from typing import Protocol

from app.features.scanner.domain.scan_item import PopupDismissMode


class InputGateway(Protocol):
    """Port para automação de área de transferência, teclado e alertas sonoros."""

    def send_code(
        self,
        *,
        code: str,
        clean_before: bool,
        dismiss_mode: PopupDismissMode | None,
    ) -> bool: ...

    def dismiss_and_clean(self, *, dismiss_mode: PopupDismissMode) -> None: ...

    def beep(self, *, frequency: int, duration_ms: int) -> None: ...
