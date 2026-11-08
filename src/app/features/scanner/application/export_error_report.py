from collections.abc import Sequence
from pathlib import Path

from app.features.scanner.domain.code_repository import CodeRepository
from app.features.scanner.domain.scan_item import ScanItem, ScanStatus
from app.shared.errors import AppError, ErrorCode


class ExportErrorReport:
    """Caso de uso: exporta todos os itens marcados com erro para uma planilha Excel."""

    def __init__(self, *, repository: CodeRepository) -> None:
        self._repository = repository

    def __call__(self, *, items: Sequence[ScanItem], output_path: Path) -> Path:
        error_items = [item for item in items if item.status == ScanStatus.ERROR]
        if not error_items:
            raise AppError(ErrorCode.VALIDATION, "There are no error items to export")

        return self._repository.export_errors(error_items, output_path)
