from pathlib import Path

import openpyxl

from app.features.scanner.domain.scan_item import mark_item_error
from app.features.scanner.infra.openpyxl_code_repository import OpenpyxlCodeRepository


def test_loads_and_exports_excel_files(tmp_path: Path) -> None:
    input_path = tmp_path / "codigo.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(["Código Waybill"])
    ws.append(["AJ260908106954601"])
    ws.append(["AJ260908106954602"])
    wb.save(input_path)

    repo = OpenpyxlCodeRepository()
    loaded = repo.load_codes(input_path)

    assert len(loaded) == 2
    assert loaded[0].code == "AJ260908106954601"

    err_item = mark_item_error(loaded[0], timestamp="14:00:00", reason="Erro de teste")
    report_path = tmp_path / "relatorio_erros.xlsx"
    repo.export_errors([err_item], report_path)

    assert report_path.is_file()
    wb_out = openpyxl.load_workbook(report_path, data_only=True)
    ws_out = wb_out.active
    assert ws_out is not None
    rows = list(ws_out.iter_rows(values_only=True))
    assert len(rows) == 2
    assert rows[1][1] == "AJ260908106954601"
