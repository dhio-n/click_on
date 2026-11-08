from collections.abc import Callable

from app.features.scanner.domain.input_gateway import InputGateway
from app.features.scanner.domain.scan_item import (
    PopupDismissMode,
    ScanItem,
    mark_item_sent,
)


class ProcessScanItem:
    """Caso de uso: executa a rotina anti-erro + colagem de um código e marca como enviado."""

    def __init__(
        self,
        *,
        input_gateway: InputGateway,
        now_str: Callable[[], str],
    ) -> None:
        self._input_gateway = input_gateway
        self._now_str = now_str

    def __call__(
        self,
        *,
        item: ScanItem,
        clean_before: bool,
        dismiss_mode: PopupDismissMode | None,
    ) -> tuple[ScanItem, bool]:
        copied = self._input_gateway.send_code(
            code=item.code,
            clean_before=clean_before,
            dismiss_mode=dismiss_mode,
        )
        updated_item = mark_item_sent(item, timestamp=self._now_str())
        return updated_item, copied
