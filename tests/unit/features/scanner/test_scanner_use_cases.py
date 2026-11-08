from pathlib import Path

import pytest

from app.features.scanner.application.export_error_report import ExportErrorReport
from app.features.scanner.application.flag_scan_error import FlagScanError
from app.features.scanner.application.load_scan_codes import LoadScanCodes
from app.features.scanner.application.process_scan_item import ProcessScanItem
from app.features.scanner.domain.scan_item import (
    PopupDismissMode,
    ScanStatus,
    create_scan_item,
    mark_item_sent,
)
from app.features.scanner.infra.fake_input_gateway import FakeInputGateway
from app.features.scanner.infra.in_memory_code_repository import InMemoryCodeRepository
from app.shared.errors import AppError, ErrorCode


def test_loads_valid_codes_from_repository(tmp_path: Path) -> None:
    excel_file = tmp_path / "codigo.xlsx"
    excel_file.write_text("placeholder", encoding="utf-8")
    repo = InMemoryCodeRepository(
        {excel_file: ["Cabeçalho", "AJ260908106954601", "AJ260908106954602"]}
    )
    use_case = LoadScanCodes(repository=repo)

    items = use_case(file_path=excel_file)

    assert len(items) == 2
    assert items[0].code == "AJ260908106954601"
    assert items[1].index == 2


def test_process_scan_item_sends_code_and_marks_sent() -> None:
    gateway = FakeInputGateway()
    use_case = ProcessScanItem(input_gateway=gateway, now_str=lambda: "12:30:00")
    item = create_scan_item(index=1, raw_code="AJ260908106954601")

    updated, copied = use_case(
        item=item,
        clean_before=True,
        dismiss_mode=PopupDismissMode.ESC_ENTER,
    )

    assert copied is True
    assert updated.status == ScanStatus.SENT
    assert updated.timestamp == "12:30:00"
    assert len(gateway.sent_codes) == 1
    assert gateway.sent_codes[0].clean_before is True


def test_flags_last_sent_item_as_error_and_dismisses_popup() -> None:
    gateway = FakeInputGateway()
    use_case = FlagScanError(input_gateway=gateway, now_str=lambda: "12:35:00")
    items = [
        mark_item_sent(
            create_scan_item(index=1, raw_code="AJ260908106954601"), timestamp="12:31:00"
        ),
        create_scan_item(index=2, raw_code="AJ260908106954602"),
    ]

    idx, updated = use_case.flag_last_sent(
        items=items,
        up_to_index=1,
        dismiss_mode=PopupDismissMode.ESC_ONLY,
    )

    assert idx == 0
    assert updated.status == ScanStatus.ERROR
    assert gateway.dismiss_calls == [PopupDismissMode.ESC_ONLY]


def test_exports_only_error_items(tmp_path: Path) -> None:
    repo = InMemoryCodeRepository()
    use_case = ExportErrorReport(repository=repo)
    gateway = FakeInputGateway()
    flagger = FlagScanError(input_gateway=gateway, now_str=lambda: "12:40:00")

    err_item = flagger.mark_item(
        item=create_scan_item(index=1, raw_code="AJ260908106954601"),
        reason="Ponto divergente",
    )
    ok_item = mark_item_sent(
        create_scan_item(index=2, raw_code="AJ260908106954602"),
        timestamp="12:39:00",
    )
    out_file = tmp_path / "erros.xlsx"

    saved_path = use_case(items=[err_item, ok_item], output_path=out_file)

    assert saved_path == out_file
    assert len(repo.exported_reports[out_file]) == 1
    assert repo.exported_reports[out_file][0].code == "AJ260908106954601"


def test_export_raises_validation_error_when_no_error_items_exist(tmp_path: Path) -> None:
    repo = InMemoryCodeRepository()
    use_case = ExportErrorReport(repository=repo)
    ok_item = create_scan_item(index=1, raw_code="AJ260908106954601")

    with pytest.raises(AppError) as exc_info:
        use_case(items=[ok_item], output_path=tmp_path / "erros.xlsx")

    assert exc_info.value.code == ErrorCode.VALIDATION
