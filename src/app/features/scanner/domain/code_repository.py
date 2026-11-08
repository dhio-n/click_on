from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from app.features.scanner.domain.scan_item import ScanItem


class CodeRepository(Protocol):
    """Port para leitura de códigos de entrada e exportação de relatórios de erro."""

    def load_codes(self, file_path: Path) -> list[ScanItem]: ...

    def export_errors(self, items: Sequence[ScanItem], output_path: Path) -> Path: ...
