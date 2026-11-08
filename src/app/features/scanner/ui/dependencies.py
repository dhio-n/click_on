import time
import tkinter as tk
from dataclasses import dataclass

from app.features.scanner.application.export_error_report import ExportErrorReport
from app.features.scanner.application.flag_scan_error import FlagScanError
from app.features.scanner.application.load_scan_codes import LoadScanCodes
from app.features.scanner.application.process_scan_item import ProcessScanItem
from app.features.scanner.infra.openpyxl_code_repository import OpenpyxlCodeRepository
from app.features.scanner.infra.win32_input_gateway import Win32InputGateway
from app.features.scanner.ui.scanner_window import AnjunAutoScannerApp
from app.shared.config import Settings, get_settings


def _current_time_str() -> str:
    return time.strftime("%H:%M:%S")


@dataclass(frozen=True, slots=True)
class ScannerDependencies:
    """Contêiner de dependências injetadas na janela principal."""

    settings: Settings
    input_gateway: Win32InputGateway
    load_scan_codes: LoadScanCodes
    process_scan_item: ProcessScanItem
    flag_scan_error: FlagScanError
    export_error_report: ExportErrorReport


def build_scanner_dependencies(settings: Settings | None = None) -> ScannerDependencies:
    """Monta os casos de uso e adapters concretos da feature scanner."""
    resolved_settings = settings or get_settings()
    repository = OpenpyxlCodeRepository()
    input_gateway = Win32InputGateway()

    return ScannerDependencies(
        settings=resolved_settings,
        input_gateway=input_gateway,
        load_scan_codes=LoadScanCodes(repository=repository),
        process_scan_item=ProcessScanItem(
            input_gateway=input_gateway,
            now_str=_current_time_str,
        ),
        flag_scan_error=FlagScanError(
            input_gateway=input_gateway,
            now_str=_current_time_str,
        ),
        export_error_report=ExportErrorReport(repository=repository),
    )


def run_scanner_app(settings: Settings | None = None) -> None:
    """Inicializa o loop principal Tkinter com as dependências injetadas."""
    deps = build_scanner_dependencies(settings)
    root = tk.Tk()
    AnjunAutoScannerApp(
        root=root,
        settings=deps.settings,
        input_gateway=deps.input_gateway,
        load_scan_codes=deps.load_scan_codes,
        process_scan_item=deps.process_scan_item,
        flag_scan_error=deps.flag_scan_error,
        export_error_report=deps.export_error_report,
    )
    root.mainloop()
