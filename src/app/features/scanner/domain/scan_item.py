from collections.abc import Sequence
from dataclasses import dataclass, replace
from enum import StrEnum

from app.shared.errors import AppError, ErrorCode

MIN_GENERIC_CODE_LENGTH = 8
MIN_WAYBILL_CODE_LENGTH = 4
WAYBILL_PREFIX = "AJ"


class ScanStatus(StrEnum):
    """Status possíveis de um código na fila de bipagem."""

    PENDING = "Pendente"
    SENDING = "Enviando..."
    SENT = "Enviado"
    ERROR = "Erro"


class PopupDismissMode(StrEnum):
    """Modos suportados para fechamento de popups de inconsistência."""

    ESC_ENTER = "ESC + Enter"
    ESC_ONLY = "Apenas ESC"
    ENTER_ONLY = "Apenas Enter"
    SPACE = "Espaço"


@dataclass(frozen=True, slots=True)
class ScanItem:
    """Entidade que representa um código Waybill na fila de bipagem."""

    index: int
    code: str
    status: ScanStatus = ScanStatus.PENDING
    timestamp: str = ""
    error_reason: str = ""


@dataclass(frozen=True, slots=True)
class ScanStats:
    """Métricas consolidadas da sessão de bipagem."""

    total: int
    sent: int
    errors: int
    pending: int
    progress_pct: float


def is_valid_waybill_code(raw_value: str) -> bool:
    """Verifica se uma string corresponde ao formato esperado de Waybill."""
    clean = raw_value.strip()
    if not clean or " " in clean:
        return False
    if clean.startswith(WAYBILL_PREFIX):
        return len(clean) >= MIN_WAYBILL_CODE_LENGTH
    has_digit = any(char.isdigit() for char in clean)
    return len(clean) >= MIN_GENERIC_CODE_LENGTH and has_digit


def create_scan_item(*, index: int, raw_code: str) -> ScanItem:
    """Cria um ScanItem validado a partir do código bruto."""
    if index < 1:
        raise AppError(ErrorCode.VALIDATION, "Item index must be at least 1")

    clean_code = raw_code.strip()
    if not is_valid_waybill_code(clean_code):
        raise AppError(ErrorCode.VALIDATION, f"Invalid waybill code: '{raw_code}'")

    return ScanItem(index=index, code=clean_code, status=ScanStatus.PENDING)


def mark_item_sending(item: ScanItem) -> ScanItem:
    """Transiciona o item para o estado 'Enviando...'."""
    return replace(item, status=ScanStatus.SENDING)


def mark_item_sent(item: ScanItem, *, timestamp: str) -> ScanItem:
    """Transiciona o item para o estado 'Enviado' limpando qualquer erro anterior."""
    return replace(item, status=ScanStatus.SENT, timestamp=timestamp, error_reason="")


def mark_item_error(item: ScanItem, *, timestamp: str, reason: str) -> ScanItem:
    """Transiciona o item para o estado 'Erro' com horário e motivo."""
    clean_reason = reason.strip() or "Inconsistência no ponto de entrega"
    return replace(item, status=ScanStatus.ERROR, timestamp=timestamp, error_reason=clean_reason)


def calculate_stats(items: Sequence[ScanItem]) -> ScanStats:
    """Calcula os contadores e percentual de progresso da fila."""
    total = len(items)
    if total == 0:
        return ScanStats(total=0, sent=0, errors=0, pending=0, progress_pct=0.0)

    sent = sum(1 for item in items if item.status == ScanStatus.SENT)
    errors = sum(1 for item in items if item.status == ScanStatus.ERROR)
    pending = sum(1 for item in items if item.status == ScanStatus.PENDING)
    done = sent + errors
    progress_pct = (done / total) * 100.0
    return ScanStats(
        total=total,
        sent=sent,
        errors=errors,
        pending=pending,
        progress_pct=progress_pct,
    )
