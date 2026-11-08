import pytest

from app.features.scanner.domain.scan_item import (
    ScanStatus,
    calculate_stats,
    create_scan_item,
    is_valid_waybill_code,
    mark_item_error,
    mark_item_sending,
    mark_item_sent,
)
from app.shared.errors import AppError, ErrorCode


def test_validates_waybill_codes_correctly() -> None:
    assert is_valid_waybill_code("AJ260908106954601") is True
    assert is_valid_waybill_code("BR12345678") is True
    assert is_valid_waybill_code(" Código Waybill ") is False
    assert is_valid_waybill_code("CURTO") is False


def test_creates_scan_item_with_pending_status() -> None:
    item = create_scan_item(index=1, raw_code="  AJ260908106954601  ")

    assert item.index == 1
    assert item.code == "AJ260908106954601"
    assert item.status == ScanStatus.PENDING


def test_rejects_invalid_scan_item_code() -> None:
    with pytest.raises(AppError) as exc_info:
        create_scan_item(index=1, raw_code="invalido")

    assert exc_info.value.code == ErrorCode.VALIDATION


def test_transitions_item_states_and_calculates_stats() -> None:
    item_1 = create_scan_item(index=1, raw_code="AJ260908106954601")
    item_2 = create_scan_item(index=2, raw_code="AJ260908106954602")
    item_3 = create_scan_item(index=3, raw_code="AJ260908106954603")

    item_1 = mark_item_sent(mark_item_sending(item_1), timestamp="10:00:01")
    item_2 = mark_item_error(item_2, timestamp="10:00:05", reason="Bloqueio de rota")

    stats = calculate_stats([item_1, item_2, item_3])

    assert stats.total == 3
    assert stats.sent == 1
    assert stats.errors == 1
    assert stats.pending == 1
    assert stats.progress_pct == pytest.approx(66.666, rel=1e-2)
