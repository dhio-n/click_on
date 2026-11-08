from collections.abc import Callable, Sequence

from app.features.scanner.domain.input_gateway import InputGateway
from app.features.scanner.domain.scan_item import (
    PopupDismissMode,
    ScanItem,
    ScanStatus,
    mark_item_error,
)
from app.shared.errors import AppError, ErrorCode


class FlagScanError:
    """Caso de uso: marca um item (ou o último enviado) como erro e limpa o navegador."""

    def __init__(
        self,
        *,
        input_gateway: InputGateway,
        now_str: Callable[[], str],
    ) -> None:
        self._input_gateway = input_gateway
        self._now_str = now_str

    def mark_item(
        self,
        *,
        item: ScanItem,
        reason: str = "Inconsistência no ponto de entrega",
    ) -> ScanItem:
        return mark_item_error(item, timestamp=self._now_str(), reason=reason)

    def flag_last_sent(
        self,
        *,
        items: Sequence[ScanItem],
        up_to_index: int,
        dismiss_mode: PopupDismissMode,
        reason: str = "Inconsistência no ponto de entrega",
    ) -> tuple[int, ScanItem]:
        upper_bound = min(up_to_index, len(items) - 1)
        for idx in range(upper_bound, -1, -1):
            candidate = items[idx]
            if candidate.status in (ScanStatus.SENT, ScanStatus.SENDING):
                updated = self.mark_item(item=candidate, reason=reason)
                self._input_gateway.dismiss_and_clean(dismiss_mode=dismiss_mode)
                return idx, updated

        raise AppError(ErrorCode.NOT_FOUND, "No recently sent code available to flag as error")
