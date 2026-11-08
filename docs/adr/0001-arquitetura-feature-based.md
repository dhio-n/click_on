# ADR 0001: Arquitetura feature-based com camadas internas

- **Status:** aceito
- **Data:** 2026-11-08

## Contexto

Padronizar o projeto ClickOn seguindo o modelo arquitetural `ai-project-template-python`,
separando regras de negócio, casos de uso, infraestrutura (Excel/Win32) e interface gráfica.

## Decisão

Organizar o código por feature (`src/app/features/scanner/`) com as camadas `domain`,
`application`, `infra` e `ui`; `shared/` para configurações e erros padronizados; e
composition root em `src/app/main.py`. As fronteiras são impostas pelo `import-linter`.

## Consequências

- Domínio e casos de uso 100% testáveis em memória sem abrir janelas Tkinter nem simular teclado real do Windows.
- Contratos verificados automaticamente via `poetry run poe check`.
