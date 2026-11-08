from pathlib import Path

from app.features.scanner.domain.code_repository import CodeRepository
from app.features.scanner.domain.scan_item import ScanItem
from app.shared.errors import AppError, ErrorCode


class LoadScanCodes:
    """Caso de uso: carrega e valida a lista de códigos a partir de uma planilha."""

    def __init__(self, *, repository: CodeRepository) -> None:
        self._repository = repository

    def __call__(self, *, file_path: Path) -> list[ScanItem]:
        if not file_path.is_file():
            raise AppError(ErrorCode.NOT_FOUND, f"Spreadsheet not found: {file_path}")

        items = self._repository.load_codes(file_path)
        if not items:
            raise AppError(
                ErrorCode.VALIDATION,
                "No valid waybill codes were found in the spreadsheet",
            )
        return items
