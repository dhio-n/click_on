import logging
import threading
import time
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from app.features.scanner.application.export_error_report import ExportErrorReport
from app.features.scanner.application.flag_scan_error import FlagScanError
from app.features.scanner.application.load_scan_codes import LoadScanCodes
from app.features.scanner.application.process_scan_item import ProcessScanItem
from app.features.scanner.domain.scan_item import (
    PopupDismissMode,
    ScanItem,
    ScanStatus,
    calculate_stats,
    mark_item_sending,
    mark_item_sent,
)
from app.features.scanner.infra.win32_input_gateway import (
    VK_ESCAPE,
    VK_F8,
    VK_F9,
    VK_F10,
    Win32InputGateway,
)
from app.shared.config import Settings
from app.shared.errors import AppError

logger = logging.getLogger(__name__)


class AnjunAutoScannerApp:
    """Interface gráfica Desktop para automação de bipagem Anjun Express."""

    def __init__(
        self,
        *,
        root: tk.Tk,
        settings: Settings,
        input_gateway: Win32InputGateway,
        load_scan_codes: LoadScanCodes,
        process_scan_item: ProcessScanItem,
        flag_scan_error: FlagScanError,
        export_error_report: ExportErrorReport,
    ) -> None:
        self.root = root
        self._settings = settings
        self._input_gateway = input_gateway
        self._load_scan_codes = load_scan_codes
        self._process_scan_item = process_scan_item
        self._flag_scan_error = flag_scan_error
        self._export_error_report = export_error_report

        self.root.title("Anjun Express - Auto Bipador & Validador (Anti-Erro)")
        self.root.geometry("860x720")
        self.root.minsize(780, 620)

        self.base_dir: Path = settings.base_dir
        self.excel_path: Path = settings.default_excel_path

        self.codes: list[ScanItem] = []
        self.current_idx: int = 0
        self.is_running: bool = False
        self.is_paused: bool = False
        self.thread: threading.Thread | None = None
        self.countdown_remaining: int = 0

        self.setup_styles()
        self.build_ui()

        if self.excel_path.is_file():
            self.load_excel(self.excel_path)

        self.hotkey_running = True
        self.hotkey_thread = threading.Thread(target=self.global_hotkey_listener, daemon=True)
        self.hotkey_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        self.c_bg = "#F3F4F6"
        self.c_card = "#FFFFFF"
        self.c_primary = "#2563EB"
        self.c_success = "#16A34A"
        self.c_warning = "#D97706"
        self.c_danger = "#DC2626"
        self.c_text = "#1F2937"

        self.root.configure(bg=self.c_bg)

        style.configure("TFrame", background=self.c_bg)
        style.configure("Card.TFrame", background=self.c_card, relief="flat")
        style.configure(
            "TLabel", background=self.c_bg, foreground=self.c_text, font=("Segoe UI", 9)
        )
        style.configure(
            "Card.TLabel", background=self.c_card, foreground=self.c_text, font=("Segoe UI", 9)
        )
        style.configure(
            "Title.TLabel",
            background=self.c_bg,
            foreground="#111827",
            font=("Segoe UI", 13, "bold"),
        )
        style.configure(
            "Subtitle.TLabel", background=self.c_bg, foreground="#4B5563", font=("Segoe UI", 9)
        )
        style.configure(
            "StatNum.TLabel",
            background=self.c_card,
            font=("Segoe UI", 16, "bold"),
            foreground=self.c_text,
        )
        style.configure(
            "StatTitle.TLabel", background=self.c_card, font=("Segoe UI", 8), foreground="#6B7280"
        )
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=24)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def build_ui(self) -> None:
        header_frame = ttk.Frame(self.root, padding="12 10 12 4")
        header_frame.pack(fill=tk.X)

        title_box = ttk.Frame(header_frame)
        title_box.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(
            title_box, text="⚡ Anjun Express - Bipagem Automática", style="Title.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            title_box,
            text="Com Limpeza Anti-Acúmulo de Erro & Fechamento de Popups",
            style="Subtitle.TLabel",
        ).pack(anchor="w")

        top_opts = ttk.Frame(header_frame)
        top_opts.pack(side=tk.RIGHT, fill=tk.Y)

        self.always_on_top_var = tk.BooleanVar(value=self._settings.always_on_top)
        self.root.attributes("-topmost", self._settings.always_on_top)
        chk_top = tk.Checkbutton(
            top_opts,
            text="📌 Sempre no Topo",
            variable=self.always_on_top_var,
            command=self.toggle_always_on_top,
            bg=self.c_bg,
            activebackground=self.c_bg,
            font=("Segoe UI", 9),
        )
        chk_top.pack(side=tk.RIGHT, padx=5)

        stats_frame = ttk.Frame(self.root, padding="12 2 12 6")
        stats_frame.pack(fill=tk.X)
        stats_frame.columnconfigure((0, 1, 2, 3), weight=1)

        c1 = ttk.Frame(stats_frame, style="Card.TFrame", padding="8 6")
        c1.grid(row=0, column=0, padx=4, sticky="nsew")
        ttk.Label(c1, text="TOTAL NA PLANILHA", style="StatTitle.TLabel").pack()
        self.lbl_total = ttk.Label(c1, text="0", style="StatNum.TLabel")
        self.lbl_total.pack()

        c2 = ttk.Frame(stats_frame, style="Card.TFrame", padding="8 6")
        c2.grid(row=0, column=1, padx=4, sticky="nsew")
        ttk.Label(c2, text="ENVIADOS", style="StatTitle.TLabel").pack()
        self.lbl_sent = ttk.Label(c2, text="0", style="StatNum.TLabel", foreground=self.c_success)
        self.lbl_sent.pack()

        c3 = ttk.Frame(stats_frame, style="Card.TFrame", padding="8 6")
        c3.grid(row=0, column=2, padx=4, sticky="nsew")
        ttk.Label(c3, text="ERROS / FALHAS", style="StatTitle.TLabel").pack()
        self.lbl_errors = ttk.Label(c3, text="0", style="StatNum.TLabel", foreground=self.c_danger)
        self.lbl_errors.pack()

        c4 = ttk.Frame(stats_frame, style="Card.TFrame", padding="8 6")
        c4.grid(row=0, column=3, padx=4, sticky="nsew")
        ttk.Label(c4, text="PENDENTES", style="StatTitle.TLabel").pack()
        self.lbl_pending = ttk.Label(
            c4, text="0", style="StatNum.TLabel", foreground=self.c_primary
        )
        self.lbl_pending.pack()

        prog_frame = ttk.Frame(self.root, padding="12 0 12 6")
        prog_frame.pack(fill=tk.X)

        curr_box = ttk.Frame(prog_frame, style="Card.TFrame", padding="8 6")
        curr_box.pack(fill=tk.X)

        top_prog = ttk.Frame(curr_box, style="Card.TFrame")
        top_prog.pack(fill=tk.X)
        self.lbl_curr_title = ttk.Label(
            top_prog,
            text="Aguardando início...",
            style="Card.TLabel",
            font=("Segoe UI", 10, "bold"),
        )
        self.lbl_curr_title.pack(side=tk.LEFT)
        self.lbl_pct = ttk.Label(
            top_prog,
            text="0%",
            style="Card.TLabel",
            font=("Segoe UI", 10, "bold"),
            foreground=self.c_primary,
        )
        self.lbl_pct.pack(side=tk.RIGHT)

        self.progress_bar = ttk.Progressbar(curr_box, orient=tk.HORIZONTAL, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(4, 0))

        ctrl_frame = ttk.Frame(self.root, padding="12 2 12 6")
        ctrl_frame.pack(fill=tk.X)

        config_box = ttk.Frame(ctrl_frame)
        config_box.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(config_box, text="⏱ Delay entre Envios (s):", font=("Segoe UI", 9, "bold")).pack(
            side=tk.LEFT
        )
        self.delay_var = tk.DoubleVar(value=self._settings.default_delay_seconds)
        delay_spin = ttk.Spinbox(
            config_box, from_=0.3, to=10.0, increment=0.2, textvariable=self.delay_var, width=5
        )
        delay_spin.pack(side=tk.LEFT, padx=(5, 10))

        for delay_preset in (1.0, 1.5, 2.0, 3.0):
            btn_d = tk.Button(
                config_box,
                text=f"{delay_preset}s",
                command=self._make_delay_setter(delay_preset),
                relief="groove",
                font=("Segoe UI", 8),
                padx=3,
                pady=0,
                bg="#E5E7EB",
            )
            btn_d.pack(side=tk.LEFT, padx=1)

        ttk.Label(config_box, text="⏳ Espera ao Iniciar:", font=("Segoe UI", 9)).pack(
            side=tk.LEFT, padx=(12, 4)
        )
        self.countdown_var = tk.IntVar(value=self._settings.default_countdown_seconds)
        cd_spin = ttk.Spinbox(
            config_box, from_=1, to=15, increment=1, textvariable=self.countdown_var, width=4
        )
        cd_spin.pack(side=tk.LEFT)
        ttk.Label(
            config_box,
            text="s (tempo para focar o campo)",
            font=("Segoe UI", 8),
            foreground="#6B7280",
        ).pack(side=tk.LEFT, padx=4)

        anti_error_box = ttk.Frame(ctrl_frame)
        anti_error_box.pack(fill=tk.X, pady=(2, 6))

        self.clean_field_var = tk.BooleanVar(value=True)
        chk_clean = tk.Checkbutton(
            anti_error_box,
            text="🧹 Limpar barra antes de colar (Ctrl+A + Del) [NUNCA acumula]",
            variable=self.clean_field_var,
            bg=self.c_bg,
            activebackground=self.c_bg,
            font=("Segoe UI", 9, "bold"),
            fg="#1E40AF",
        )
        chk_clean.pack(side=tk.LEFT, padx=(0, 12))

        self.auto_close_popup_var = tk.BooleanVar(value=True)
        chk_popup = tk.Checkbutton(
            anti_error_box,
            text="❌ Fechar popup de inconsistência",
            variable=self.auto_close_popup_var,
            bg=self.c_bg,
            activebackground=self.c_bg,
            font=("Segoe UI", 9, "bold"),
            fg="#B91C1C",
        )
        chk_popup.pack(side=tk.LEFT, padx=(0, 6))

        self.popup_mode_var = tk.StringVar(value=PopupDismissMode.ESC_ENTER.value)
        cmb_mode = ttk.Combobox(
            anti_error_box,
            textvariable=self.popup_mode_var,
            values=[mode.value for mode in PopupDismissMode],
            width=12,
            state="readonly",
        )
        cmb_mode.pack(side=tk.LEFT)

        btn_bar = ttk.Frame(ctrl_frame)
        btn_bar.pack(fill=tk.X, pady=(2, 0))

        self.btn_start = tk.Button(
            btn_bar,
            text="▶ INICIAR (F8)",
            command=self.action_start,
            bg="#16A34A",
            fg="white",
            activebackground="#15803D",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_pause = tk.Button(
            btn_bar,
            text="⏸ PAUSAR (F9)",
            command=self.action_pause,
            state=tk.DISABLED,
            bg="#D97706",
            fg="white",
            activebackground="#B45309",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
        )
        self.btn_pause.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_stop = tk.Button(
            btn_bar,
            text="⏹ PARAR (ESC)",
            command=self.action_stop,
            state=tk.DISABLED,
            bg="#DC2626",
            fg="white",
            activebackground="#B91C1C",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 10))

        btn_manual_clean = tk.Button(
            btn_bar,
            text="🧹 Fechar Popup e Limpar (F10)",
            command=self.action_manual_dismiss_clean,
            bg="#EEF2FF",
            fg="#3730A3",
            activebackground="#E0E7FF",
            font=("Segoe UI", 9, "bold"),
            relief="groove",
            padx=8,
            pady=5,
            cursor="hand2",
        )
        btn_manual_clean.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_flag_error = tk.Button(
            btn_bar,
            text="⚠️ Marcar Último como Erro",
            command=self.action_flag_last_error,
            bg="#FEE2E2",
            fg="#991B1B",
            activebackground="#FECACA",
            font=("Segoe UI", 9, "bold"),
            relief="groove",
            padx=8,
            pady=5,
            cursor="hand2",
        )
        self.btn_flag_error.pack(side=tk.LEFT, padx=(0, 6))

        btn_load = tk.Button(
            btn_bar,
            text="📂 Trocar Planilha",
            command=self.action_choose_excel,
            bg="#E5E7EB",
            fg="#1F2937",
            font=("Segoe UI", 9),
            relief="groove",
            padx=8,
            pady=5,
            cursor="hand2",
        )
        btn_load.pack(side=tk.RIGHT)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=(6, 10))

        tab_main = ttk.Frame(notebook)
        notebook.add(tab_main, text="📋 Todos os Códigos")
        self.setup_table_tab(tab_main)

        tab_errors = ttk.Frame(notebook)
        notebook.add(tab_errors, text="⚠️ Códigos com Erro")
        self.setup_errors_tab(tab_errors)

        tab_log = ttk.Frame(notebook)
        notebook.add(tab_log, text="📜 Histórico / Logs")
        self.setup_log_tab(tab_log)

        self.status_bar = ttk.Label(
            self.root,
            text="Pronto. Carregue os códigos e clique em Iniciar.",
            font=("Segoe UI", 8),
            foreground="#4B5563",
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 4))

    def setup_table_tab(self, parent: ttk.Frame) -> None:
        top_bar = ttk.Frame(parent, padding="4 4 4 4")
        top_bar.pack(fill=tk.X)
        tip_text = (
            "Dica: Clique com o botão direito para iniciar de um código "
            "específico ou marcar status."
        )
        ttk.Label(
            top_bar,
            text=tip_text,
            font=("Segoe UI", 8),
            foreground="#6B7280",
        ).pack(side=tk.LEFT)

        cols = ("idx", "code", "status", "time", "note")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("idx", text="#")
        self.tree.heading("code", text="Código do Pacote / Waybill")
        self.tree.heading("status", text="Status")
        self.tree.heading("time", text="Horário")
        self.tree.heading("note", text="Observações / Detalhes")

        self.tree.column("idx", width=50, anchor="center")
        self.tree.column("code", width=180, anchor="w")
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("time", width=80, anchor="center")
        self.tree.column("note", width=250, anchor="w")

        self.tree.tag_configure("pending", background="#FFFFFF", foreground="#4B5563")
        self.tree.tag_configure(
            "active", background="#DBEAFE", foreground="#1E40AF", font=("Segoe UI", 9, "bold")
        )
        self.tree.tag_configure("sent", background="#DCFCE7", foreground="#166534")
        self.tree.tag_configure(
            "error", background="#FEE2E2", foreground="#991B1B", font=("Segoe UI", 9, "bold")
        )

        scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(
            label="▶ Iniciar a partir deste código", command=self.set_start_from_selected
        )
        self.context_menu.add_command(
            label="⚠️ Marcar como Erro / Inconsistência", command=self.set_selected_as_error
        )
        self.context_menu.add_command(
            label="✅ Marcar como Enviado", command=self.set_selected_as_sent
        )
        self.tree.bind("<Button-3>", self.show_context_menu)

    def setup_errors_tab(self, parent: ttk.Frame) -> None:
        top_err = ttk.Frame(parent, padding="6 4")
        top_err.pack(fill=tk.X)

        ttk.Label(
            top_err, text="Lista de itens marcados com inconsistência/erro.", font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        btn_export = tk.Button(
            top_err,
            text="💾 Exportar Erros para Excel",
            command=self.export_errors_excel,
            bg="#E5E7EB",
            fg="#111827",
            font=("Segoe UI", 8, "bold"),
            relief="groove",
            padx=6,
            pady=2,
            cursor="hand2",
        )
        btn_export.pack(side=tk.RIGHT)

        cols = ("idx", "code", "time", "note")
        self.tree_err = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        self.tree_err.heading("idx", text="#")
        self.tree_err.heading("code", text="Código do Pacote / Waybill")
        self.tree_err.heading("time", text="Horário")
        self.tree_err.heading("note", text="Detalhes do Erro")

        self.tree_err.column("idx", width=60, anchor="center")
        self.tree_err.column("code", width=200, anchor="w")
        self.tree_err.column("time", width=90, anchor="center")
        self.tree_err.column("note", width=350, anchor="w")

        scroll_err = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree_err.yview)
        self.tree_err.configure(yscrollcommand=scroll_err.set)

        self.tree_err.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_err.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_log_tab(self, parent: ttk.Frame) -> None:
        self.log_text = tk.Text(
            parent, font=("Consolas", 9), bg="#1E293B", fg="#E2E8F0", wrap=tk.WORD
        )
        scroll_log = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll_log.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y)

    def log(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        self.log_text.insert(tk.END, line)
        self.log_text.see(tk.END)
        logger.info(msg)

    def _make_delay_setter(self, value: float) -> Callable[[], None]:
        def _setter() -> None:
            self.delay_var.set(value)

        return _setter

    def toggle_always_on_top(self) -> None:
        self.root.attributes("-topmost", self.always_on_top_var.get())

    def show_context_menu(self, event: tk.Event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _selected_index(self) -> int | None:
        selected = self.tree.selection()
        if not selected:
            return None
        values = self.tree.item(selected[0], "values")
        if not values:
            return None
        idx = int(values[0]) - 1
        return idx if 0 <= idx < len(self.codes) else None

    def set_start_from_selected(self) -> None:
        idx = self._selected_index()
        if idx is None:
            return
        self.current_idx = idx
        self.update_stats()
        code = self.codes[idx].code
        self.log(f"Ponto de início alterado para o código #{idx + 1}: {code}")
        self.lbl_curr_title.config(text=f"Próximo: {code} (#{idx + 1} de {len(self.codes)})")

    def set_selected_as_error(self) -> None:
        idx = self._selected_index()
        if idx is None:
            return
        self.mark_as_error(idx, "Inconsistência no ponto de entrega (Marcado pelo operador)")

    def set_selected_as_sent(self) -> None:
        idx = self._selected_index()
        if idx is None:
            return
        self.codes[idx] = mark_item_sent(self.codes[idx], timestamp=time.strftime("%H:%M:%S"))
        self.update_tree_row(idx)
        self.update_stats()

    def _current_dismiss_mode(self) -> PopupDismissMode:
        raw = self.popup_mode_var.get()
        for mode in PopupDismissMode:
            if mode.value == raw:
                return mode
        return PopupDismissMode.ESC_ENTER

    def action_manual_dismiss_clean(self) -> None:
        mode = self._current_dismiss_mode()
        self._input_gateway.dismiss_and_clean(dismiss_mode=mode)
        self.log(f"Comando manual: Popup fechado ({mode.value}) e barra limpa.")

    def load_excel(self, file_path: Path | str) -> None:
        resolved_path = Path(file_path)
        try:
            self.log(f"Abrindo planilha: {resolved_path}")
            self.codes = self._load_scan_codes(file_path=resolved_path)
            self.current_idx = 0
            self.excel_path = resolved_path

            for row in self.tree.get_children():
                self.tree.delete(row)
            for row in self.tree_err.get_children():
                self.tree_err.delete(row)

            for item in self.codes:
                self.tree.insert(
                    "",
                    tk.END,
                    iid=str(item.index),
                    values=(item.index, item.code, item.status.value, "", ""),
                    tags=("pending",),
                )

            self.update_stats()
            self.log(f"Sucesso! {len(self.codes)} códigos carregados da planilha.")
            self.status_bar.config(
                text=f"Planilha carregada: {resolved_path.name} ({len(self.codes)} códigos)."
            )
            self.lbl_curr_title.config(text=f"Pronto para iniciar. 1º Código: {self.codes[0].code}")
        except AppError as exc:
            messagebox.showwarning("Aviso", exc.message)
            self.log(f"Aviso ao carregar planilha: {exc.message}")
        except Exception as exc:
            messagebox.showerror(
                "Erro ao carregar planilha", f"Não foi possível ler o arquivo:\n{exc}"
            )
            self.log(f"ERRO ao ler planilha: {exc}")

    def action_choose_excel(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=str(self.base_dir),
            title="Selecione a planilha com códigos",
            filetypes=[("Planilhas Excel", "*.xlsx;*.xls"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self.load_excel(Path(path))

    def update_tree_row(self, idx: int) -> None:
        item = self.codes[idx]
        iid = str(item.index)
        tag = "pending"
        if item.status == ScanStatus.SENT:
            tag = "sent"
        elif item.status == ScanStatus.ERROR:
            tag = "error"
        elif item.status == ScanStatus.SENDING:
            tag = "active"

        self.tree.item(
            iid,
            values=(item.index, item.code, item.status.value, item.timestamp, item.error_reason),
            tags=(tag,),
        )

    def update_stats(self) -> None:
        stats = calculate_stats(self.codes)
        self.lbl_total.config(text=str(stats.total))
        self.lbl_sent.config(text=str(stats.sent))
        self.lbl_errors.config(text=str(stats.errors))
        self.lbl_pending.config(text=str(stats.pending))

        if stats.total > 0:
            done = stats.sent + stats.errors
            self.progress_bar["maximum"] = stats.total
            self.progress_bar["value"] = done
            self.lbl_pct.config(text=f"{stats.progress_pct:.1f}% ({done}/{stats.total})")
        else:
            self.progress_bar["value"] = 0
            self.lbl_pct.config(text="0%")

    def mark_as_error(self, idx: int, reason: str = "Inconsistência no ponto de entrega") -> None:
        if 0 <= idx < len(self.codes):
            updated = self._flag_scan_error.mark_item(item=self.codes[idx], reason=reason)
            self.codes[idx] = updated
            self.update_tree_row(idx)

            iid_err = f"err_{updated.index}"
            row_values = (updated.index, updated.code, updated.timestamp, updated.error_reason)
            if not self.tree_err.exists(iid_err):
                self.tree_err.insert("", tk.END, iid=iid_err, values=row_values)
            else:
                self.tree_err.item(iid_err, values=row_values)

            self.update_stats()
            self.log(f"⚠️ MARCADO COM ERRO: #{updated.index} - {updated.code} ({reason})")

    def action_flag_last_error(self) -> None:
        try:
            idx, updated = self._flag_scan_error.flag_last_sent(
                items=self.codes,
                up_to_index=self.current_idx,
                dismiss_mode=self._current_dismiss_mode(),
            )
            self.codes[idx] = updated
            self.update_tree_row(idx)
            iid_err = f"err_{updated.index}"
            row_values = (updated.index, updated.code, updated.timestamp, updated.error_reason)
            if not self.tree_err.exists(iid_err):
                self.tree_err.insert("", tk.END, iid=iid_err, values=row_values)
            else:
                self.tree_err.item(iid_err, values=row_values)
            self.update_stats()
            self.log(
                f"⚠️ MARCADO COM ERRO: #{updated.index} - {updated.code} ({updated.error_reason})"
            )
            messagebox.showinfo(
                "Marcado com Erro",
                f"Código {updated.code} (#{idx + 1}) marcado como ERRO e popup fechado!",
            )
        except AppError:
            messagebox.showwarning("Aviso", "Nenhum código enviado recentemente para marcar.")

    def action_start(self) -> None:
        if not self.codes:
            messagebox.showwarning("Aviso", "Carregue uma planilha com códigos antes de iniciar.")
            return

        if self.is_running and self.is_paused:
            self.is_paused = False
            self.btn_pause.config(text="⏸ PAUSAR (F9)", bg="#D97706")
            self.status_bar.config(text="Execução retomada...")
            self.log("Execução retomada pelo usuário.")
            return

        if self.is_running:
            return

        self.is_running = True
        self.is_paused = False

        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL, text="⏸ PAUSAR (F9)")
        self.btn_stop.config(state=tk.NORMAL)

        self.countdown_remaining = self.countdown_var.get()
        self.run_countdown()

    def run_countdown(self) -> None:
        if not self.is_running:
            return

        if self.countdown_remaining > 0:
            msg = (
                "ATENÇÃO: Clique na barra de bipagem no navegador! "
                f"Iniciando em {self.countdown_remaining} segundos..."
            )
            self.status_bar.config(text=msg)
            self.lbl_curr_title.config(
                text=f"⏳ PREPARE-SE: Clique na barra da página em {self.countdown_remaining}s..."
            )
            self._input_gateway.beep(frequency=1000, duration_ms=150)
            self.countdown_remaining -= 1
            self.root.after(1000, self.run_countdown)
        else:
            self.status_bar.config(
                text="Robô em execução: colando com limpeza anti-acúmulo e Enter..."
            )
            self._input_gateway.beep(frequency=1800, duration_ms=250)
            self.thread = threading.Thread(target=self.worker_loop, daemon=True)
            self.thread.start()

    def _wait_configured_delay(self) -> None:
        delay = max(0.2, self.delay_var.get())
        elapsed = 0.0
        step = 0.05
        while elapsed < delay and self.is_running:
            if self.is_paused:
                break
            time.sleep(step)
            elapsed += step

    def _highlight_sending_row(self, idx: int, code: str, iid: str) -> None:
        self.update_tree_row(idx)
        self.lbl_curr_title.config(text=f"Bipando: {code} (#{idx + 1} de {len(self.codes)})")
        self.tree.see(iid)
        self.tree.selection_set(iid)

    def worker_loop(self) -> None:
        while self.is_running and self.current_idx < len(self.codes):
            if self.is_paused:
                time.sleep(0.1)
                continue

            item = self.codes[self.current_idx]
            if item.status == ScanStatus.SENT:
                self.current_idx += 1
                continue

            idx = self.current_idx
            sending_item = mark_item_sending(item)
            self.codes[idx] = sending_item
            iid = str(sending_item.index)
            self.root.after(0, self._highlight_sending_row, idx, sending_item.code, iid)

            dismiss_mode = self._current_dismiss_mode() if self.auto_close_popup_var.get() else None
            updated_item, copied = self._process_scan_item(
                item=sending_item,
                clean_before=self.clean_field_var.get(),
                dismiss_mode=dismiss_mode,
            )
            if not copied:
                self.root.after(
                    0, self.log, f"Falha ao copiar código {sending_item.code} para o clipboard."
                )

            self.codes[idx] = updated_item
            self.root.after(0, self.update_tree_row, idx)
            self.root.after(0, self.update_stats)
            self.root.after(0, self.log, f"Enviado #{idx + 1}: {updated_item.code}")

            self.current_idx += 1
            self._wait_configured_delay()

        if self.current_idx >= len(self.codes):
            self.root.after(0, self.on_finished)

    def on_finished(self) -> None:
        self.is_running = False
        self.is_paused = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED, text="⏸ PAUSAR (F9)")
        self.btn_stop.config(state=tk.DISABLED)
        self.lbl_curr_title.config(text="✅ Processamento concluído!")
        self.status_bar.config(text="Todos os códigos da lista foram processados.")
        self.log("🏁 Processo finalizado com sucesso!")
        self._input_gateway.beep(frequency=2000, duration_ms=400)
        messagebox.showinfo("Concluído", "Todos os códigos da planilha foram processados!")

    def action_pause(self) -> None:
        if not self.is_running:
            return
        if not self.is_paused:
            self.is_paused = True
            self.btn_pause.config(text="▶ CONTINUAR (F9)", bg="#16A34A")
            self.status_bar.config(
                text="⏸ PAUSADO. Verifique o Anjun. Pressione F9 para retomar ou F10 para limpar."
            )
            self.log("Execução PAUSADA pelo usuário.")
        else:
            self.is_paused = False
            self.btn_pause.config(text="⏸ PAUSAR (F9)", bg="#D97706")
            self.status_bar.config(text="Retomando...")
            self.log("Execução RETOMADA.")

    def action_stop(self) -> None:
        self.is_running = False
        self.is_paused = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED, text="⏸ PAUSAR (F9)")
        self.btn_stop.config(state=tk.DISABLED)
        self.status_bar.config(text="⏹ Parado pelo operador.")
        self.lbl_curr_title.config(text="Execução parada.")
        self.log("Execução PARADA pelo usuário.")

    def _poll_hotkey_transitions(
        self,
        *,
        last_f8: bool,
        last_f9: bool,
        last_f10: bool,
        last_esc: bool,
    ) -> tuple[bool, bool, bool, bool]:
        f8_state = self._input_gateway.is_key_pressed(VK_F8)
        if f8_state and not last_f8:
            if not self.is_running:
                self.root.after(0, self.action_start)
            elif self.is_paused:
                self.root.after(0, self.action_pause)

        f9_state = self._input_gateway.is_key_pressed(VK_F9)
        if f9_state and not last_f9 and self.is_running:
            self.root.after(0, self.action_pause)

        f10_state = self._input_gateway.is_key_pressed(VK_F10)
        if f10_state and not last_f10:
            self.root.after(0, self.action_manual_dismiss_clean)

        esc_state = self._input_gateway.is_key_pressed(VK_ESCAPE)
        if esc_state and not last_esc and self.is_running:
            self.root.after(0, self.action_stop)

        return f8_state, f9_state, f10_state, esc_state

    def global_hotkey_listener(self) -> None:
        last_f8 = False
        last_f9 = False
        last_f10 = False
        last_esc = False

        while self.hotkey_running:
            try:
                last_f8, last_f9, last_f10, last_esc = self._poll_hotkey_transitions(
                    last_f8=last_f8,
                    last_f9=last_f9,
                    last_f10=last_f10,
                    last_esc=last_esc,
                )
                time.sleep(0.04)
            except Exception:
                time.sleep(0.1)

    def export_errors_excel(self) -> None:
        save_path = self.base_dir / f"relatorio_erros_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
        try:
            saved = self._export_error_report(items=self.codes, output_path=save_path)
            messagebox.showinfo("Sucesso", f"Relatório de erros salvo em:\n{saved}")
            self.log(f"Relatório de erros salvo: {saved}")
        except AppError as exc:
            messagebox.showinfo("Exportar", exc.message)
        except Exception as exc:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo:\n{exc}")

    def on_close(self) -> None:
        self.hotkey_running = False
        self.is_running = False
        self.root.destroy()
