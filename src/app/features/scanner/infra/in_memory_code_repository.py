from collections.abc import Sequence
from pathlib import Path

from app.features.scanner.domain.scan_item import (
    ScanItem,
    create_scan_item,
    is_valid_waybill_code,
)


class InMemoryCodeRepository:
    """Fake em memória para testes unitários de leitura e exportação de códigos."""

    def __init__(self, raw_rows_by_path: dict[Path, list[str]] | None = None) -> None:
        self._raw_rows_by_path: dict[Path, list[str]] = raw_rows_by_path or {}
        self.exported_reports: dict[Path, list[ScanItem]] = {}

    def load_codes(self, file_path: Path) -> list[ScanItem]:
        rows = self._raw_rows_by_path.get(file_path, [])
        items: list[ScanItem] = []
        for raw in rows:
            if is_valid_waybill_code(raw):
                items.append(create_scan_item(index=len(items) + 1, raw_code=raw))
        return items

    def export_errors(self, items: Sequence[ScanItem], output_path: Path) -> Path:
        self.exported_reports[output_path] = list(items)
        return output_path
