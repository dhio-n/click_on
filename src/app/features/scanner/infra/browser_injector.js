/**
 * Script de Injeção Visual Direta no Navegador (Console F12 ou Tampermonkey)
 * Página: https://manage.anjunexpress.com/expressDataCenter/sortingManagement/SortingOperation/scanBagging
 * 
 * ATUALIZAÇÃO ANTI-ERRO:
 * - Limpa a barra completamente antes de cada bipagem (NUNCA acumula códigos).
 * - Detecta o popup "Inconsistência no ponto de entrega" e fecha automaticamente.
 * - Registra os erros visualmente na lista.
 */

(function () {
    if (document.getElementById('anjun-auto-panel')) {
        document.getElementById('anjun-auto-panel').remove();
    }

    const panel = document.createElement('div');
    panel.id = 'anjun-auto-panel';
    panel.style.position = 'fixed';
    panel.style.top = '15px';
    panel.style.right = '15px';
    panel.style.width = '380px';
    panel.style.maxHeight = '92vh';
    panel.style.backgroundColor = '#ffffff';
    panel.style.boxShadow = '0 10px 28px rgba(0,0,0,0.35)';
    panel.style.borderRadius = '10px';
    panel.style.zIndex = '999999';
    panel.style.fontFamily = 'Segoe UI, Arial, sans-serif';
    panel.style.fontSize = '12px';
    panel.style.color = '#333';
    panel.style.display = 'flex';
    panel.style.flexDirection = 'column';
    panel.style.border = '2px solid #2563eb';
    panel.style.overflow = 'hidden';

    panel.innerHTML = `
        <div style="background: #2563eb; color: #fff; padding: 10px 14px; font-weight: bold; font-size: 13px; display: flex; justify-content: space-between; align-items: center; cursor: move;" id="anjun-panel-header">
            <span>⚡ Anjun Bipador (Anti-Inconsistência)</span>
            <button id="anjun-btn-close" style="background:none; border:none; color:#fff; font-size:16px; cursor:pointer;">✖</button>
        </div>
        <div style="padding: 12px; display: flex; flex-direction: column; gap: 8px; overflow-y: auto;">
            <div>
                <label style="font-weight: bold;">Delay entre envios (ms):</label>
                <div style="display:flex; gap: 6px; margin-top: 4px;">
                    <input type="number" id="anjun-delay" value="1500" step="100" min="400" style="width: 80px; padding: 4px 6px; border: 1px solid #ccc; border-radius: 4px;" />
                    <button class="anjun-quick-delay" data-d="1000" style="padding: 2px 8px; border: 1px solid #ddd; border-radius: 4px; cursor:pointer;">1s</button>
                    <button class="anjun-quick-delay" data-d="1500" style="padding: 2px 8px; border: 1px solid #ddd; border-radius: 4px; cursor:pointer;">1.5s</button>
                    <button class="anjun-quick-delay" data-d="2000" style="padding: 2px 8px; border: 1px solid #ddd; border-radius: 4px; cursor:pointer;">2s</button>
                </div>
            </div>

            <!-- Opções Anti-Erro -->
            <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 8px; display: flex; flex-direction: column; gap: 4px;">
                <label style="font-weight: bold; color: #1e40af;">
                    <input type="checkbox" id="anjun-chk-clean" checked /> 🧹 Limpar barra antes de colar (Anti-Acúmulo)
                </label>
                <label style="font-weight: bold; color: #b91c1c;">
                    <input type="checkbox" id="anjun-chk-dismiss" checked /> ❌ Fechar popup de inconsistência auto
                </label>
            </div>

            <div>
                <label style="font-weight: bold;">Lista de Códigos (um por linha):</label>
                <textarea id="anjun-codes" rows="4" placeholder="Cole aqui os códigos ou carregue o arquivo .txt..." style="width: 100%; box-sizing: border-box; font-family: monospace; font-size: 11px; padding: 6px; border: 1px solid #ccc; border-radius: 4px; resize: vertical;"></textarea>
            </div>

            <div style="display: flex; gap: 6px;">
                <input type="file" id="anjun-file-input" accept=".txt,.csv" style="display: none;" />
                <button id="anjun-btn-file" style="flex: 1; padding: 6px; background: #f3f4f6; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; font-size: 11px;">📂 Carregar .TXT</button>
                <button id="anjun-btn-clear" style="padding: 6px 12px; background: #f3f4f6; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; font-size: 11px;">Limpar</button>
                <button id="anjun-btn-dismiss-now" style="padding: 6px 10px; background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: bold;">Fechar Popup</button>
            </div>

            <div style="display: flex; gap: 6px; margin-top: 4px;">
                <button id="anjun-btn-start" style="flex: 2; padding: 8px; background: #16a34a; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">▶ INICIAR</button>
                <button id="anjun-btn-pause" style="flex: 1; padding: 8px; background: #d97706; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;" disabled>⏸ PAUSAR</button>
                <button id="anjun-btn-stop" style="flex: 1; padding: 8px; background: #dc2626; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;" disabled>⏹ PARAR</button>
            </div>

            <!-- Progresso e Status -->
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;">
                <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 4px;">
                    <span id="anjun-status-text">Pronto</span>
                    <span id="anjun-progress-pct">0%</span>
                </div>
                <div style="background: #e2e8f0; border-radius: 4px; height: 10px; overflow: hidden;">
                    <div id="anjun-progress-bar" style="background: #2563eb; width: 0%; height: 100%; transition: width 0.2s;"></div>
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 6px; font-size: 11px;">
                    <span>Total: <strong id="anjun-cnt-total">0</strong></span>
                    <span style="color: #16a34a;">Enviados: <strong id="anjun-cnt-ok">0</strong></span>
                    <span style="color: #dc2626;">Erros: <strong id="anjun-cnt-err">0</strong></span>
                </div>
            </div>

            <!-- Log -->
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: bold;">Histórico & Erros:</span>
                <button id="anjun-btn-export" style="background:none; border:none; color:#2563eb; cursor:pointer; font-size:11px; text-decoration:underline;">Exportar Erros</button>
            </div>
            <div id="anjun-log" style="height: 120px; overflow-y: auto; background: #1e293b; color: #f8fafc; font-family: monospace; font-size: 10px; padding: 6px; border-radius: 4px; line-height: 1.4;">
                <div>[Aguardando início...]</div>
            </div>
        </div>
    `;

    document.body.appendChild(panel);

    let isRunning = false;
    let isPaused = false;
    let codeList = [];
    let errorList = [];
    let currentIndex = 0;
    let totalSent = 0;
    let totalErrors = 0;

    const txtCodes = document.getElementById('anjun-codes');
    const inputDelay = document.getElementById('anjun-delay');
    const chkClean = document.getElementById('anjun-chk-clean');
    const chkDismiss = document.getElementById('anjun-chk-dismiss');
    const btnStart = document.getElementById('anjun-btn-start');
    const btnPause = document.getElementById('anjun-btn-pause');
    const btnStop = document.getElementById('anjun-btn-stop');
    const btnClose = document.getElementById('anjun-btn-close');
    const btnDismissNow = document.getElementById('anjun-btn-dismiss-now');
    const btnExport = document.getElementById('anjun-btn-export');
    const lblStatus = document.getElementById('anjun-status-text');
    const lblPct = document.getElementById('anjun-progress-pct');
    const barProg = document.getElementById('anjun-progress-bar');
    const cntTotal = document.getElementById('anjun-cnt-total');
    const cntOk = document.getElementById('anjun-cnt-ok');
    const cntErr = document.getElementById('anjun-cnt-err');
    const divLog = document.getElementById('anjun-log');
    const fileInput = document.getElementById('anjun-file-input');

    btnClose.onclick = () => panel.remove();

    document.querySelectorAll('.anjun-quick-delay').forEach(btn => {
        btn.onclick = () => inputDelay.value = btn.getAttribute('data-d');
    });

    document.getElementById('anjun-btn-file').onclick = () => fileInput.click();
    fileInput.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (event) => {
            txtCodes.value = event.target.result;
            updateCountFromText();
        };
        reader.readAsText(file);
    };

    document.getElementById('anjun-btn-clear').onclick = () => {
        txtCodes.value = '';
        updateCountFromText();
    };

    txtCodes.oninput = updateCountFromText;

    function updateCountFromText() {
        const lines = txtCodes.value.split('\n').map(s => s.trim()).filter(s => s.length > 0);
        cntTotal.innerText = lines.length;
    }

    function addLog(msg, isError = false) {
        const d = new Date();
        const time = d.toTimeString().split(' ')[0];
        const line = document.createElement('div');
        line.style.color = isError ? '#f87171' : '#a7f3d0';
        line.innerText = `[${time}] ${msg}`;
        divLog.appendChild(line);
        divLog.scrollTop = divLog.scrollHeight;
    }

    // Função para fechar qualquer popup de inconsistência ou confirmação
    function dismissOpenPopups() {
        let found = false;
        // 1. Botões do Element-UI message-box ou dialog
        const buttons = document.querySelectorAll(
            '.el-message-box__btns button, ' +
            '.el-message-box__btns .el-button--primary, ' +
            '.el-dialog__footer button, ' +
            '.el-dialog__headerbtn, ' +
            '.el-message-box__headerbtn'
        );
        for (let btn of buttons) {
            if (btn.offsetParent !== null) { // Visível na tela
                btn.click();
                found = true;
            }
        }
        
        // 2. Disparar tecla ESC no documento como fallback
        document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', keyCode: 27, which: 27, bubbles: true }));
        document.dispatchEvent(new KeyboardEvent('keyup', { key: 'Escape', code: 'Escape', keyCode: 27, which: 27, bubbles: true }));

        return found;
    }

    btnDismissNow.onclick = () => {
        dismissOpenPopups();
        addLog("Comando: Popup fechado manualmente.");
    };

    function findTargetInput() {
        const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([disabled])'));
        for (let inp of inputs) {
            const ph = (inp.placeholder || '').toLowerCase();
            const aria = (inp.getAttribute('aria-label') || '').toLowerCase();
            if (ph.includes('waybill') || ph.includes('código') || ph.includes('bip') || ph.includes('código de barras') || ph.includes('pacote') || aria.includes('waybill')) {
                return inp;
            }
        }
        for (let inp of inputs) {
            if (inp.offsetParent !== null && inp.type === 'text') {
                return inp;
            }
        }
        return inputs[0] || null;
    }

    // Monitorar e fechar popups de erro automaticamente via MutationObserver
    const observer = new MutationObserver((mutations) => {
        if (!chkDismiss.checked) return;
        for (let mutation of mutations) {
            for (let node of mutation.addedNodes) {
                if (node.nodeType === 1) {
                    const txt = (node.innerText || '').toLowerCase();
                    if (txt.includes('inconsistência') || txt.includes('inconsistencia') || txt.includes('ponto de entrega') || txt.includes('erro') || txt.includes('falha')) {
                        addLog(`⚠️ Alerta na tela: ${node.innerText.trim().slice(0, 70)}`, true);
                        setTimeout(() => {
                            dismissOpenPopups();
                        }, 100);
                    }
                }
            }
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    async function sendCode(code) {
        const input = findTargetInput();
        if (!input) {
            addLog("❌ Barra de entrada não encontrada na tela!", true);
            return false;
        }

        // 1. Fechar popup se estiver aberto
        if (chkDismiss.checked) {
            dismissOpenPopups();
            await new Promise(r => setTimeout(r, 60));
        }

        input.focus();
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;

        // 2. LIMPAR A BARRA ANTES DE COLAR (ANTI-ACÚMULO)
        if (chkClean.checked) {
            nativeSetter.call(input, '');
            input.dispatchEvent(new Event('input', { bubbles: true }));
            await new Promise(r => setTimeout(r, 30));
        }

        // 3. Colar o novo código
        nativeSetter.call(input, code);
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));

        await new Promise(r => setTimeout(r, 60));

        // 4. Disparar Enter
        ['keydown', 'keypress', 'keyup'].forEach(type => {
            input.dispatchEvent(new KeyboardEvent(type, {
                key: 'Enter',
                code: 'Enter',
                keyCode: 13,
                which: 13,
                bubbles: true,
                cancelable: true
            }));
        });

        return true;
    }

    async function processLoop() {
        while (isRunning && currentIndex < codeList.length) {
            if (isPaused) {
                await new Promise(r => setTimeout(r, 200));
                continue;
            }

            const code = codeList[currentIndex];
            lblStatus.innerText = `Bipando ${currentIndex + 1}/${codeList.length}`;
            
            const ok = await sendCode(code);
            if (ok) {
                totalSent++;
                cntOk.innerText = totalSent;
                addLog(`Enviado: ${code}`);
            } else {
                totalErrors++;
                cntErr.innerText = totalErrors;
                errorList.push(code);
                addLog(`Erro ao enviar: ${code}`, true);
            }

            currentIndex++;
            const pct = Math.round((currentIndex / codeList.length) * 100);
            lblPct.innerText = `${pct}%`;
            barProg.style.width = `${pct}%`;

            const delay = parseInt(inputDelay.value, 10) || 1500;
            await new Promise(r => setTimeout(r, delay));
        }

        if (currentIndex >= codeList.length) {
            lblStatus.innerText = "✅ Concluído!";
            addLog("🏁 Processamento de todos os códigos finalizado!");
            stop();
        }
    }

    function start() {
        codeList = txtCodes.value.split('\n').map(s => s.trim()).filter(s => s.length > 0);
        if (codeList.length === 0) {
            alert("Cole ou carregue ao menos um código antes de iniciar.");
            return;
        }

        isRunning = true;
        isPaused = false;
        currentIndex = 0;
        totalSent = 0;
        totalErrors = 0;
        errorList = [];
        cntTotal.innerText = codeList.length;
        cntOk.innerText = "0";
        cntErr.innerText = "0";

        btnStart.disabled = true;
        btnPause.disabled = false;
        btnStop.disabled = false;
        txtCodes.disabled = true;

        addLog(`Iniciando ${codeList.length} códigos com limpeza anti-acúmulo...`);
        processLoop();
    }

    function pause() {
        if (!isRunning) return;
        isPaused = !isPaused;
        if (isPaused) {
            btnPause.innerText = "▶ RETOMAR";
            lblStatus.innerText = "⏸ Pausado";
            addLog("Pausado pelo usuário.");
        } else {
            btnPause.innerText = "⏸ PAUSAR";
            lblStatus.innerText = "Executando...";
            addLog("Retomado.");
        }
    }

    function stop() {
        isRunning = false;
        isPaused = false;
        btnStart.disabled = false;
        btnPause.disabled = true;
        btnPause.innerText = "⏸ PAUSAR";
        btnStop.disabled = true;
        txtCodes.disabled = false;
    }

    btnExport.onclick = () => {
        if (errorList.length === 0) {
            alert("Nenhum erro registrado até o momento.");
            return;
        }
        const blob = new Blob([errorList.join('\n')], { type: 'text/plain;charset=utf-8' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `erros_inconsistencia_${Date.now()}.txt`;
        a.click();
    };

    btnStart.onclick = start;
    btnPause.onclick = pause;
    btnStop.onclick = stop;

    // Arrastar painel
    const header = document.getElementById('anjun-panel-header');
    let isDragging = false, startX, startY, initialLeft, initialTop;
    header.onmousedown = (e) => {
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        const rect = panel.getBoundingClientRect();
        initialLeft = rect.left;
        initialTop = rect.top;
        document.onmousemove = (ev) => {
            if (!isDragging) return;
            panel.style.left = `${initialLeft + (ev.clientX - startX)}px`;
            panel.style.top = `${initialTop + (ev.clientY - startY)}px`;
            panel.style.right = 'auto';
        };
        document.onmouseup = () => { isDragging = false; document.onmousemove = null; };
    };

    addLog("Painel pronto com limpeza anti-acúmulo ativa!");
})();
