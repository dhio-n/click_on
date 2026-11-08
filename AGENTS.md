# AGENTS.md — Regras do projeto para agentes de IA

> Este arquivo é a **fonte única de verdade** para qualquer IA que trabalhe neste repositório
> (Claude Code, Cursor, Copilot, Codex, Gemini...). Leia-o inteiro antes de qualquer tarefa.
> Em caso de conflito entre um pedido e estas regras, **pare e pergunte**.

## 1. Antes de escrever qualquer código

1. Leia `docs/PROJECT.md` (o que o sistema faz, glossário do domínio) e `docs/ARCHITECTURE.md`.
2. **Procure antes de criar.** Busque no código funções, classes e padrões parecidos com o que
   você vai escrever (`src/app/shared/`, a feature atual e features vizinhas). Reutilize ou estenda.
3. Para tarefas com mais de ~3 arquivos, apresente um **plano curto** antes: arquivos que serão
   criados/alterados, onde cada coisa vai morar e o que será reutilizado.
4. Se o pedido for ambíguo, pergunte. Não invente requisitos.

## 2. Stack

- Python 3.12+, Tkinter (GUI Desktop), Win32 API via `ctypes`, OpenPyXL (planilhas Excel), Pydantic v2 + pydantic-settings.
- Dependências: **Poetry** (`poetry add <pkg>` / `poetry add --group dev <pkg>`).
- Qualidade: ruff (lint + formatação), mypy `strict`, import-linter (arquitetura), pytest.
- Tarefas: `poetry run poe <tarefa>` (ver `[tool.poe.tasks]` no `pyproject.toml`).
- **Não adicione dependências** sem justificar (o que resolve, alternativa na stdlib,
  manutenção). Decisões relevantes viram um ADR em `docs/adr/`.

## 3. Arquitetura (resumo — detalhes em `docs/ARCHITECTURE.md`)

```
src/app/
  features/<feature>/          # uma pasta por capacidade de negócio (vertical slice), snake_case
    domain/                    # entidades (dataclass), regras puras, ports (Protocol). Sem I/O, sem GUI.
    application/               # casos de uso: orquestram domain + ports. Um arquivo por caso de uso.
    infra/                     # adapters concretos (OpenPyXL, Win32 API ctypes, fakes em memória).
    ui/                        # interface gráfica Tkinter e ligação de dependências (dependencies.py).
    __init__.py                # API pública da feature.
  shared/                      # código usado por 2+ features: config, errors.
  main.py                      # composition root: inicializa configurações e abre a aplicação.
tests/unit/features/<feature>/ e tests/integration/
```

**Regra de dependência** (imposta pelo import-linter — `poetry run poe arch` falha se violada):
`ui -> application | infra -> domain`. O `domain` não importa `tkinter`, `openpyxl` nem `ctypes`.
`application` não importa `infra` nem `ui`. `shared` nunca importa `features`. Features não
importam umas às outras.

Ao criar uma feature, **registre-a nos contratos `[FEATURES]` do `pyproject.toml`**. Crie apenas
as camadas que a feature **precisa**.

## 4. Regras contra código descartável (as mais importantes)

1. **Regra de três:** não crie abstração (helper genérico, classe base, factory, Protocol
   com uma única implementação "para o futuro") até o padrão aparecer **3 vezes**. Duas cópias
   parecidas são aceibáveis; uma abstração errada é cara.
   - Exceção: ports (`Protocol`) em `domain/` para I/O (repositórios Excel, gateways Win32) — existem para testabilidade.
2. **YAGNI:** implemente só o que foi pedido. Sem parâmetros opcionais, flags ou configurações
   "caso precise depois".
3. **Proibido** módulos genéricos sem dono: `utils.py`, `helpers.py`, `common/`, `misc/`, `base.py`
   genérico. Todo código mora na feature que o usa. Só vai para `shared/` quando uma **segunda**
   feature precisar — e aí é **movido** (não copiado).
4. **Sem código morto:** nada de funções não usadas, código comentado, `print`, TODO sem contexto.
5. **Não reescreva o que existe.** Se algo existente quase serve, estenda-o; se não serve,
   explique por quê antes de criar uma alternativa.
6. **Mudanças mínimas:** não refatore, renomeie ou reformate código fora do escopo da tarefa.

## 5. Convenções (detalhes em `docs/CONVENTIONS.md`)

- Módulos, pastas, funções e variáveis em `snake_case`; classes em `PascalCase`; constantes em
  `UPPER_SNAKE_CASE`. Arquivos com papel explícito: `scan_item.py`, `code_repository.py`,
  `load_scan_codes.py`, `openpyxl_code_repository.py`, `scanner_window.py`, `test_*.py`.
- Código, identificadores e mensagens de erro internas em **inglês**; documentação e textos da UI em **português**.
- **Type hints em tudo** (mypy strict). Proibido `Any` e `# type: ignore` sem justificativa no comentário.
- Funções pequenas (≈ até 30 linhas); parâmetros keyword-only (`*`) quando houver mais de 2.
- **Erros:** falha esperada -> `raise AppError(ErrorCode.X, "message")` (`app/shared/errors.py`).
  Nunca `except: pass`.
- **DI:** casos de uso recebem dependências no `__init__`; `ui/dependencies.py` instancia os adapters concretos.
- Configuração só via `app/shared/config.py` (`Settings`). Logs com `logging`, nunca `print`.

## 6. Testes

- Regra de negócio nova ou bug corrigido => teste primeiro (ou junto). Bug: o teste que falha vem antes.
- Unitários em `tests/unit/features/<feature>/` usando adapters em memória — **sem mocks**
  quando um fake simples resolve.
- Integração em `tests/integration/` testando leitura/escrita real de planilhas em diretório temporário (`tmp_path`).
- Teste comportamento, não implementação. Funções `test_<comportamento>`; Arrange/Act/Assert.

## 7. Definition of Done

- [ ] `poetry run poe check` passa (lint + formato + mypy + arquitetura + testes).
- [ ] Sem duplicação de algo que já existia nem abstração especulativa.
- [ ] Nenhum arquivo fora do escopo alterado sem motivo.
- [ ] `docs/PROJECT.md` / `docs/ARCHITECTURE.md` atualizados se mudou algo neles; ADR para decisão nova.
- [ ] Commit em Conventional Commits (`feat(scanner): ...`, `fix: ...`, `refactor: ...`).

Ao terminar, informe: o que mudou, o que foi reutilizado, o resultado do `poe check`
e pendências. **Nunca** diga que passou se não executou.
