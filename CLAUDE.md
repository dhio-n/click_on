# CLAUDE.md

@AGENTS.md

## Específico do Claude Code

- **Agentes** (`.claude/agents/`): `architect` (planeja, não escreve código), `test-writer`,
  `implementer`, `reviewer`, `refactorer`.
- **Comandos** (`.claude/commands/`):
  - `/nova-feature <descrição>` — fluxo completo: plano -> testes -> implementação -> revisão.
  - `/revisar` — revisa as mudanças atuais contra o `AGENTS.md`.
  - `/auditar` — audita o projeto inteiro contra o padrão.
- Para tarefas não triviais, entre em plan mode antes de editar.
- Rode `poetry run poe check` antes de declarar uma tarefa concluída.
