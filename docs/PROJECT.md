# PROJECT.md — Contexto do projeto ClickOn

## Visão

O **ClickOn** é um sistema desktop de automação operacional criado para realizar a bipagem e
*bagging* em lote de pacotes (Waybills) na plataforma web da **Anjun Express**, preservando a
sessão autenticada do navegador do operador e evitando erros de acúmulo de códigos no campo de leitura.

## Escopo

**Dentro do escopo:**

- Leitura de códigos de rastreio/Waybill a partir de planilhas Excel (`codigo.xlsx`).
- Automação de teclado e área de transferência via Win32 API (`ctypes`) com limpeza preventiva da barra (`Ctrl+A` + `Backspace`).
- Fechamento automático e manual de popups/modais de inconsistência (`ESC + Enter`, `Apenas ESC`, `Apenas Enter`, `Espaço`).
- Interface gráfica Desktop em Tkinter com estatísticas em tempo real, barra de progresso, abas de códigos/erros/logs e opção "Sempre no Topo".
- Atalhos globais de teclado (`F8` iniciar/retomar, `F9` pausar/continuar, `F10` fechar popup e limpar barra, `ESC` parar).
- Exportação de relatório Excel contendo os códigos marcados com erro/inconsistência.
- Script opcional `injetor_navegador.js` para execução direta no console do navegador.

**Fora do escopo:**

- Automação via Selenium/Playwright que crie nova sessão de navegador sem os cookies do operador.
- API HTTP ou banco de dados relacional (toda persistência ocorre via planilhas Excel).

## Features implementadas

| Feature (pasta) | Responsabilidade | Status |
|---|---|---|
| `scanner` | Carregamento de planilhas de códigos, sessão de bipagem automatizada, controle de erros e interface gráfica Desktop | ativo |

## Glossário do domínio

| Termo | Significado | Nome no código |
|---|---|---|
| Waybill / Código | Código identificador do pacote (ex.: `AJ260908106954601`) | `code` / `ScanItem` |
| Sessão de Bipagem | Lista de códigos carregados com seus status e contadores | `ScanStats` / `ScanItem` |
| Limpeza Anti-Acúmulo | Seleção total (`Ctrl+A`) + exclusão (`Backspace`) antes de colar o próximo código | `clean_before` |
| Modo de Fechamento de Popup | Teclas enviadas para fechar alertas de inconsistência do navegador | `PopupDismissMode` |

## Regras de negócio importantes

- Somente células válidas (iniciadas por `AJ` ou com ao menos 8 caracteres alfanuméricos contendo dígitos e sem espaços) são importadas como códigos Waybill.
- Antes de colar (`Ctrl+V`) um código, se a proteção anti-acúmulo estiver ativa, o campo de entrada deve ser limpo (`Ctrl+A` + `Backspace`) para impedir concatenação com um código anterior recusado.
- Apenas códigos com status `ERROR` são incluídos na exportação de planilha de erros.

## Requisitos não funcionais

- **Plataforma:** Windows (uso de `ctypes.windll.user32` e `kernel32` com fallback seguro em outros ambientes para testes).
- **Performance:** Resposta imediata a atalhos globais (~40ms de polling) e interface não-bloqueante (worker em thread separada).
- **Persistência:** Arquivos `.xlsx` locais lidos e gerados via `openpyxl`.
