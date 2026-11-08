# ClickOn — Automação de Bipagem e Bagging (Anjun Express)

Aplicação desktop e automação operacional para inserção sequencial de códigos Waybill na plataforma
Anjun Express, construída com **arquitetura padronizada feature-based** (inspirada em Clean/Hexagonal
Architecture).

## O que tem aqui

| Caminho | Para quê |
|---|---|
| `AGENTS.md` | Regras que **qualquer** IA lê primeiro (fonte única de verdade). |
| `CLAUDE.md` | Importa o `AGENTS.md` + extras do Claude Code. |
| `docs/GUIA-DE-IMPLEMENTACAO.md` | Como usar o padrão no dia a dia. |
| `docs/ARCHITECTURE.md` | Camadas (`ui`, `application`, `infra`, `domain`), regras de dependência. |
| `docs/CONVENTIONS.md` | Nomes, tipos, erros, logs, testes, commits. |
| `docs/PROJECT.md` | Visão, escopo, glossário e regras de negócio do ClickOn. |
| `docs/adr/` | Registro de decisões de arquitetura. |
| `docs/prompts/` | Prompts prontos para evolução e manutenção com IA. |
| `src/app/features/scanner/` | Feature principal de bipagem automática, leitura de Excel e automação Win32. |
| `injetor_navegador.js` | Painel flutuante opcional para execução direta no console do navegador. |
| `iniciar.bat` / `app_bipador.py` | Atalhos para iniciar a interface gráfica Desktop rapidamente. |

## Início rápido

Pré-requisitos: Python 3.12+ e Poetry 2+.

```bash
poetry install
poetry run poe check      # lint + formato + mypy + arquitetura + testes
poetry run poe dev        # abre a interface gráfica Desktop
```

Ou dê duplo clique em `iniciar.bat`.

## Tarefas (`poetry run poe <tarefa>`)

| Tarefa | Faz |
|---|---|
| `dev` / `start` | Inicia a aplicação Desktop (`python -m app.main`). |
| `check` | lint + format-check + typecheck + arch + test (o "Definition of Done"). |
| `test` / `cov` | Testes / testes com cobertura. |
| `lint` / `format` | Ruff. |
| `typecheck` | mypy strict. |
| `arch` | import-linter (fronteiras de arquitetura). |
