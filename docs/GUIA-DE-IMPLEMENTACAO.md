# Guia de Implementação da Padronização — ClickOn

Este projeto segue a padronização arquitetural de projetos Python construídos com IA, adaptada
para aplicações **Desktop (Tkinter) e Automação (Win32 API + Excel)**.

## Comandos do dia a dia

```bash
poetry install          # instala dependências do projeto
poetry run poe check    # roda ruff lint, ruff format --check, mypy strict, import-linter e pytest
poetry run poe dev      # abre a aplicação Desktop
```

## Checklist para novas funcionalidades

- [ ] Criar ou estender casos de uso em `src/app/features/<feature>/application/`.
- [ ] Manter `domain/` 100% puro (sem `tkinter`, `openpyxl` ou `ctypes`).
- [ ] Implementar I/O (Excel, teclado, área de transferência) em `infra/` através de `Protocol` definido em `domain/`.
- [ ] Adicionar testes unitários em `tests/unit/features/<feature>/` usando fakes em memória.
- [ ] Garantir `poetry run poe check` verde antes de concluir.
