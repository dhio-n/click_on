from collections.abc import Sequence
from pathlib import Path

import openpyxl

from app.features.scanner.domain.scan_item import (
    ScanItem,
    create_scan_item,
    is_valid_waybill_code,
)
from app.shared.errors import AppError, ErrorCode


class OpenpyxlCodeRepository:
    """Adapter concreto que lê códigos e exporta relatórios de erro usando OpenPyXL."""

    def load_codes(self, file_path: Path) -> list[ScanItem]:
        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
        except Exception as exc:
            raise AppError(ErrorCode.IO_ERROR, f"Failed to read Excel file: {exc}") from exc

        sheet = workbook.active
        if sheet is None:
            return []

        items: list[ScanItem] = []
        for row in sheet.iter_rows(values_only=True):
            if not row or row[0] is None:
                continue
            raw_val = str(row[0]).strip()
            if is_valid_waybill_code(raw_val):
                items.append(create_scan_item(index=len(items) + 1, raw_code=raw_val))

        return items

    def export_errors(self, items: Sequence[ScanItem], output_path: Path) -> Path:
        try:
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            if sheet is None:
                sheet = workbook.create_sheet("Erros de Bipagem")
            else:
                sheet.title = "Erros de Bipagem"

            sheet.append(["#", "Código do Pacote / Waybill", "Horário", "Motivo / Detalhes"])
            for item in items:
                sheet.append([item.index, item.code, item.timestamp, item.error_reason])

            output_path.parent.mkdir(parents=True, exist_ok=True)
            workbook.save(output_path)
            return output_path
        except Exception as exc:
            raise AppError(ErrorCode.IO_ERROR, f"Failed to save error report: {exc}") from exc
