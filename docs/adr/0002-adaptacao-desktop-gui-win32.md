# ADR 0002: Camada `ui` no lugar de `http` para aplicação Desktop

- **Status:** aceito
- **Data:** 2026-11-08

## Contexto

O template de referência utiliza uma camada `http/` (FastAPI) e banco de dados SQLAlchemy/Alembic.
O ClickOn, porém, é uma ferramenta Desktop em Tkinter que automatiza digitação via Win32 API e
lê/escreve planilhas `.xlsx`.

## Decisão

Substituir a camada de apresentação `http/` por `ui/` (Tkinter) mantendo exatamente a mesma regra
de dependência (`ui -> application | infra -> domain`) e remover dependências de servidor web e ORM
desnecessárias (YAGNI).

## Consequências

- O projeto permanece enxuto (apenas `openpyxl` e `pydantic`/`pydantic-settings` como dependências de produção).
- `iniciar.bat` e `app_bipador.py` continuam funcionando diretamente para o operador final.
