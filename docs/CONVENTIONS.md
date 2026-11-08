# Convenções

## Nomes

| Item | Padrão | Exemplo |
|---|---|---|
| Pastas de feature e módulos | `snake_case` | `scanner/`, `load_scan_codes.py` |
| Entidade | `<entidade>.py` | `scan_item.py` -> `ScanItem` |
| Port | `<entidade>_repository.py`, `<servico>_gateway.py` | `code_repository.py`, `input_gateway.py` |
| Adapter | `<tecnologia>_<papel>.py` | `openpyxl_code_repository.py`, `win32_input_gateway.py` |
| Caso de uso | `<verbo>_<objeto>.py` -> classe `<VerboObjeto>` | `load_scan_codes.py` -> `LoadScanCodes` |
| Interface Gráfica | `ui/<componente>.py` | `ui/scanner_window.py` |
| Testes | `test_<modulo>.py`, funções `test_<comportamento>` | `test_rejects_empty_spreadsheet` |
| Constantes | `UPPER_SNAKE_CASE` | `MIN_CODE_LENGTH` |
| Privados | prefixo `_` | `_is_valid_row` |

## Funções e classes

- Uma responsabilidade; ≈ até 30 linhas; complexidade ≤ 10 (ruff C90).
- Mais de 2 parâmetros -> keyword-only (`def f(*, a, b, c)`).
- Retorno antecipado em vez de `if` aninhado. Sem números/strings mágicos.
- `@dataclass(frozen=True, slots=True)` para entidades e value objects.

## Tipos

- mypy `strict` em `src/`. Sem `Any`; sem `# type: ignore` sem explicação na mesma linha.
- `X | None` em vez de `Optional[X]`; `collections.abc` para `Callable`, `Sequence`...
- Ports são `typing.Protocol`.

## Erros

| Situação | Como |
|---|---|
| Regra de negócio violada / arquivo inválido | `raise AppError(ErrorCode.X, "message")` |
| Bug / falha inesperada | Exceção tratada na camada `ui/` com `messagebox` e logada |

## Logs

`logger = logging.getLogger(__name__)`. Nunca `print` (ruff T20).
