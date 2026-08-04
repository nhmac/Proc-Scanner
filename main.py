import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pyperclip  # pip install pyperclip
from pypdf import PdfReader
import sys

# ================= CONFIGURAÇÃO =================
FONT_CONS = ("Consolas", 10)
FONT_UI = ("Segoe UI", 10)
FONT_RESUMO = ("Segoe UI", 10, "bold")


# ================= DOMÍNIO =================
def extrair_id_nome(nome_arquivo: str) -> str:
    try:
        partes = nome_arquivo.split("_")
        if len(partes) > 1:
            return partes[1]
        return ""
    except Exception:
        return ""


# ================= UI =================
class PDFAnalyzerApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Processamento · Scanner")
        self.root.geometry("1000x720")

        def resource_path(relative_path):
            """ Obtém o caminho absoluto para o recurso, funciona para dev e para PyInstaller """
            try:
                # O PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)

        # No teu __init__, usa assim:
        try:
            icon_path = resource_path("icone.ico")
            self.root.iconbitmap(icon_path)
        except:
            pass

        self.lista_ids_global = []
        self.total_analisados = 0

        ttk.Style(self.root).theme_use("vista")

        # Estrutura de Frames
        self._build_config()
        self._build_actions()
        self._build_progress()
        self._build_resumo()
        self._build_results_area()

    def _build_config(self):
        self.frame_config = ttk.LabelFrame(self.root, text="Configuração")
        self.frame_config.pack(fill="x", padx=10, pady=5)

        ttk.Label(self.frame_config, text="Pasta dos PDFs:").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.entry_pasta = ttk.Entry(self.frame_config, width=65)
        self.entry_pasta.grid(row=0, column=1, padx=5)
        ttk.Button(self.frame_config, text="Procurar", command=self.browse).grid(row=0, column=2, padx=5)

    def _build_actions(self):
        self.frame_acoes = ttk.LabelFrame(self.root, text="Ações")
        self.frame_acoes.pack(fill="x", padx=10, pady=5)

        container_botoes = ttk.Frame(self.frame_acoes)
        container_botoes.pack(fill="x", padx=10, pady=10)

        estilo_botao = {'side': 'left', 'ipady': 5, 'ipadx': 10}

        ttk.Button(container_botoes, text="Processar", command=self.start).pack(**estilo_botao)
        ttk.Button(container_botoes, text="Limpar", command=self.clear).pack(**estilo_botao, padx=10)

        self.btn_copy_all = ttk.Button(container_botoes, text="Copiar IDs", command=self.copiar_todos,
                                       state="disabled")
        self.btn_copy_all.pack(**estilo_botao)

    def _build_progress(self):
        self.frame_progresso = ttk.LabelFrame(self.root, text="Progresso")
        self.frame_progresso.pack(fill="x", padx=10, pady=5)

        self.progress = ttk.Progressbar(self.frame_progresso, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=15)

        self.lbl_percent = ttk.Label(self.frame_progresso, text="0%")
        self.lbl_percent.pack(side="left", padx=(0, 10))

    def _build_resumo(self):
        self.frame_resumo = ttk.LabelFrame(self.root, text="Resumo")
        self.frame_resumo.pack(fill="x", padx=10, pady=5)

        self.lbl_stats = ttk.Label(
            self.frame_resumo,
            text="Nenhum processamento executado",
            font=FONT_RESUMO,
            foreground="#7f8c8d"
        )
        self.lbl_stats.pack(padx=10, pady=10, anchor="w")

    def _build_results_area(self):
        frame_main = ttk.LabelFrame(self.root, text="Resultados")
        frame_main.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(frame_main, bg="#f8f9fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_main, orient="vertical", command=self.canvas.yview)
        self.container = ttk.Frame(self.canvas)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.container, anchor="nw")

        self.container.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # --- ATIVAÇÃO DO SCROLL PELO RATO ---
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)

    def _on_mousewheel(self, event):
        """Permite fazer scroll com a roda do rato"""
        # Desloca a visualização para cima ou para baixo
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def ui(self, func, *args, **kwargs):
        self.root.after(0, lambda: func(*args, **kwargs))

    def browse(self):
        pasta = filedialog.askdirectory()
        if pasta:
            self.entry_pasta.delete(0, tk.END)
            self.entry_pasta.insert(0, pasta)

    def clear(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.progress["value"] = 0
        self.lbl_percent.config(text="0%")
        self.lista_ids_global = []
        self.total_analisados = 0
        self.lbl_stats.config(text="Nenhum processamento executado", foreground="#7f8c8d")
        self.btn_copy_all.config(state="disabled")

    def atualizar_status(self):
        self.lbl_stats.config(
            text=f"Ficheiros Analisados: {self.total_analisados} | IDs Recolhidos: {len(self.lista_ids_global)}",
            foreground="#2c3e50"
        )

    def start(self):
        threading.Thread(target=self.processar, daemon=True).start()

    def copiar_todos(self):
        if self.lista_ids_global:
            texto_formatado = " OR ".join(self.lista_ids_global)
            pyperclip.copy(texto_formatado)
            messagebox.showinfo("Sucesso", "IDs copiados para o Clipboard com sucesso!")

    def processar(self):
        try:
            pasta = self.entry_pasta.get()
            if not os.path.isdir(pasta):
                raise ValueError("Por favor, selecione uma pasta válida.")

            self.ui(self.clear)
            self.ui(self.lbl_stats.config, text="A iniciar...", foreground="#2c3e50")

            arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]

            if not arquivos:
                self.ui(self.lbl_stats.config, text="Nenhum PDF encontrado na pasta.")
                return

            total_arquivos = len(arquivos)

            for idx, nome in enumerate(arquivos, start=1):
                caminho = os.path.join(pasta, nome)
                try:
                    leitor = PdfReader(caminho)
                    num_paginas = len(leitor.pages)

                    self.total_analisados += 1

                    if num_paginas == 1 or num_paginas > 2:
                        id_extraido = extrair_id_nome(nome)
                        if id_extraido:
                            self.lista_ids_global.append(id_extraido)
                            self.ui(self.adicionar_card, nome, num_paginas)

                    self.ui(self.atualizar_status)

                except Exception:
                    pass

                p = int((idx / total_arquivos) * 100)
                self.ui(self.progress.configure, value=p)
                self.ui(self.lbl_percent.config, text=f"{p}%")

            if self.lista_ids_global:
                self.ui(self.btn_copy_all.config, state="normal")

        except Exception as e:
            self.ui(messagebox.showerror, "Erro", str(e))

    def adicionar_card(self, nome, pags):
        card = ttk.Frame(self.container, relief="groove", padding=5)
        card.pack(fill="x", padx=5, pady=2)

        texto_formatado = f"{nome} -> Páginas: {pags}"
        lbl = ttk.Label(card, text=texto_formatado, font=FONT_UI)
        lbl.pack(side="left", padx=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFAnalyzerApp(root)
    root.mainloop()