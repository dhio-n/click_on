from enum import StrEnum


class ErrorCode(StrEnum):
    """Catálogo fechado de códigos de erro da aplicação."""

    VALIDATION = "VALIDATION"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    IO_ERROR = "IO_ERROR"


class AppError(Exception):
    """Falha esperada de regra de negócio ou validação."""

    def __init__(self, code: ErrorCode, message: str, details: object | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
