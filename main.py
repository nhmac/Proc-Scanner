import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pyperclip  # pip install pyperclip
from pypdf import PdfReader

import processamento_ui as ui
from processamento_ui import COR, fmt


# ================= DOMÍNIO =================
def extrair_id_nome(nome_arquivo: str) -> str:
    try:
        partes = nome_arquivo.split("_")
        if len(partes) > 1:
            return partes[1]
        return ""
    except Exception:
        return ""


# A caixa de pesquisa do Explorador do Windows 10 não aceita textos muito compridos: os IDs vão
# em grupos, pela mesma ordem, cada um com no máximo LIMITE_PESQUISA caracteres (igual à web 1.2,
# que mostra um Copiar por grupo; esta janela continua a copiar tudo de uma vez).
LIMITE_PESQUISA = 250


def grupos_pesquisa(ids, limite=LIMITE_PESQUISA):
    grupos, atual, tamanho = [], [], 0
    for id_ in ids:
        extra = 4 + len(id_) if atual else len(id_)  # " OR " + id
        if atual and tamanho + extra > limite:
            grupos.append(atual)
            atual, tamanho = [], 0
            extra = len(id_)
        tamanho += extra
        atual.append(id_)
    if atual:
        grupos.append(atual)
    return [" OR ".join(g) for g in grupos]


# ================= UI =================
class ScannerApp(ctk.CTk):

    def __init__(self):
        ui.preparar()
        super().__init__()

        ui.configurar_janela(self, "Processamento · Scanner")
        self.f = ui.criar_fontes(self)

        self.pasta_selecionada = ""
        self.lista_ids_global = []
        self.total_analisados = 0
        self.a_processar = False
        self._vazio = None
        self.setup_ui()

    # ------------------------------------------------------------------ UI --
    def setup_ui(self):
        # Sidebar
        self.sidebar = ui.sidebar(self)
        ui.cabecalho_sidebar(self.sidebar, self.f, "Scanner", "IDs de PDFs com 1 ou 3+ páginas")

        # Secção: Pasta
        ui.label_secao(self.sidebar, self.f, "PASTA").pack(anchor="w", padx=24, pady=(32, 8))

        self.btn_folder = ui.botao_secundario(self.sidebar, self.f, "Escolher pasta…", self.escolher_pasta)
        self.btn_folder.pack(padx=24, fill="x")

        chip = ui.chip(self.sidebar)
        chip.pack(padx=24, pady=(10, 0), fill="x")
        self.lbl_pasta = ctk.CTkLabel(chip, text="Nenhuma pasta selecionada", font=self.f["corpo"],
                                      text_color=COR["texto_sec"], wraplength=210, justify="left", anchor="w")
        self.lbl_pasta.pack(anchor="w", fill="x", padx=12, pady=8)
        # Só aparece depois de escolher a pasta
        self.lbl_npdfs = ctk.CTkLabel(chip, text="", font=self.f["pequeno"], text_color=COR["texto_sec"],
                                      anchor="w")

        # Secção: Ações
        ui.label_secao(self.sidebar, self.f, "AÇÕES").pack(anchor="w", padx=24, pady=(28, 8))
        self.btn_copy_all = ui.botao_secundario(self.sidebar, self.f, "Copiar IDs", self.copiar_todos,
                                                state="disabled")
        self.btn_copy_all.pack(padx=24, fill="x")
        self.btn_clear = ui.botao_link(self.sidebar, self.f, "Limpar resultados", self.clear)
        self.btn_clear.pack(anchor="w", padx=18, pady=(6, 0))

        self.btn_run = ui.botao_principal(self.sidebar, self.f, "Processar", self.start)
        self.btn_run.pack(side="bottom", pady=24, padx=24, fill="x")

        # Área Central
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=28, pady=(24, 16))
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(header, text="Resultados", font=self.f["titulo"], text_color=COR["texto"]).pack(side="left")
        self.status_lbl = ctk.CTkLabel(header, text="", font=self.f["corpo"])
        self.status_lbl.pack(side="right")

        self.progress = ui.Progresso(self.main_frame, self.f, self)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        self.progress.grid_remove()

        # Resumo
        self.resumo = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.resumo.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        self.resumo.grid_columnconfigure((0, 1, 2), weight=1, uniform="stat")
        self.stat_analisados = ui.stat_tile(self.resumo, self.f, 0, "Ficheiros analisados")
        self.stat_ids = ui.stat_tile(self.resumo, self.f, 1, "IDs recolhidos")
        self.stat_ignorados = ui.stat_tile(self.resumo, self.f, 2, "Ignorados")
        self.resumo.grid_remove()

        self.scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent",
                                             scrollbar_button_color=COR["card"],
                                             scrollbar_button_hover_color=COR["card_hover"])
        self.scroll.grid(row=3, column=0, sticky="nsew", pady=(16, 0))

        self.clear()

    def _mostrar_empty_state(self, texto="Escolha uma pasta e carregue em Processar"):
        self._vazio = ctk.CTkLabel(self.scroll, text=texto, font=self.f["corpo"], text_color=COR["texto_sec"])
        self._vazio.pack(pady=120)

    def set_status(self, texto, tipo="idle"):
        ui.definir_estado(self.status_lbl, texto, tipo)

    def _set_ocupado(self, ocupado):
        self.a_processar = ocupado
        ui.botao_ocupado(self.btn_run, ocupado, "Processar", "A processar…")
        estado = "disabled" if ocupado else "normal"
        self.btn_folder.configure(state=estado)
        self.btn_clear.configure(state=estado)
        if ocupado:
            self.btn_copy_all.configure(state="disabled")

    # -------------------------------------------------------------- Ações --
    def escolher_pasta(self):
        pasta = filedialog.askdirectory()
        if pasta:
            self.pasta_selecionada = pasta
            self.lbl_pasta.configure(text=os.path.basename(pasta), text_color=COR["texto"])
            n = len([f for f in os.listdir(pasta) if f.lower().endswith(".pdf")])
            self.lbl_npdfs.configure(text=f"{n} PDF{'s' if n != 1 else ''} encontrado{'s' if n != 1 else ''}")
            self.lbl_pasta.pack_configure(pady=(8, 0))
            self.lbl_npdfs.pack(anchor="w", fill="x", padx=12, pady=(0, 8))

    def clear(self):
        if self.a_processar:
            return
        for w in self.scroll.winfo_children():
            w.destroy()
        self.lista_ids_global = []
        self.total_analisados = 0
        self.resumo.grid_remove()
        self.btn_copy_all.configure(state="disabled")
        self.set_status("Pronto para iniciar")
        self._mostrar_empty_state()

    def start(self):
        if self.a_processar:
            return
        if not os.path.isdir(self.pasta_selecionada):
            messagebox.showwarning("Aviso", "Selecione uma pasta primeiro!")
            return

        # Limpar antes de lançar a thread: os resultados novos nunca se misturam com os antigos
        self.clear()
        self.atualizar_resumo()
        self.resumo.grid()
        self.progress.iniciar("A preparar…")
        self._set_ocupado(True)
        self.set_status("A analisar os PDFs…", "ativo")

        threading.Thread(target=self.processar, args=(self.pasta_selecionada,), daemon=True).start()

    def copiar_todos(self):
        if not self.lista_ids_global:
            return
        try:
            pyperclip.copy(" OR ".join(self.lista_ids_global))
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível copiar para o clipboard:\n\n{e}")
            return
        n = len(self.lista_ids_global)
        self.set_status(f"{n} ID{'s' if n != 1 else ''} copiado{'s' if n != 1 else ''} para o clipboard.", "ok")
        self.btn_copy_all.configure(text="Copiado ✓", text_color=COR["sucesso_texto"])
        self.after(2000, lambda: self.btn_copy_all.configure(text="Copiar IDs", text_color=COR["texto"]))

    def processar(self, pasta):
        # Corre numa thread: todas as alterações à UI e aos resultados passam por self.after
        try:
            arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]

            if not arquivos:
                self.after(0, self.terminar, "Nenhum PDF encontrado na pasta.")
                return

            total_arquivos = len(arquivos)
            analisados = 0

            for idx, nome in enumerate(arquivos, start=1):
                # Antes de ler: diz qual é o PDF; depois: a barra avança
                self.after(0, self.progress.atualizar, (idx - 1) / total_arquivos,
                           f"{fmt(idx)} de {fmt(total_arquivos)} PDFs · {nome}")
                caminho = os.path.join(pasta, nome)
                try:
                    leitor = PdfReader(caminho)
                    num_paginas = len(leitor.pages)

                    analisados += 1

                    if num_paginas == 1 or num_paginas > 2:
                        id_extraido = extrair_id_nome(nome)
                        if id_extraido:
                            self.after(0, self.adicionar_resultado, nome, num_paginas, id_extraido)

                    self.after(0, self.atualizar_resumo, analisados)

                except Exception:
                    pass

                self.after(0, self.progress.atualizar, idx / total_arquivos)

            self.after(0, self.terminar)

        except Exception as e:
            self.after(0, self.mostrar_erro, str(e))

    def atualizar_resumo(self, analisados=None):
        if analisados is not None:
            self.total_analisados = analisados
        recolhidos = len(self.lista_ids_global)
        self.stat_analisados.configure(text=fmt(self.total_analisados))
        self.stat_ids.configure(text=fmt(recolhidos))
        self.stat_ignorados.configure(text=fmt(self.total_analisados - recolhidos))

    def terminar(self, aviso=None):
        self._set_ocupado(False)
        n = len(self.lista_ids_global)
        if aviso:
            self.progress.concluir(False, "Nenhum PDF na pasta")
            self.set_status(aviso, "erro")
            return
        self.progress.concluir(True)
        if n:
            self.btn_copy_all.configure(state="normal")
        else:
            self._vazio.configure(text="Nenhum PDF com 1 ou 3+ páginas nesta pasta")
        self.set_status(f"Concluído: {n} ID{'s' if n != 1 else ''} recolhido{'s' if n != 1 else ''}.", "ok")

    def mostrar_erro(self, msg):
        self.progress.concluir(False)
        self._set_ocupado(False)
        self.set_status("Erro ao processar", "erro")
        messagebox.showerror("Erro", msg)

    # --------------------------------------------------------------- Linha --
    def adicionar_resultado(self, nome, pags, id_extraido):
        if self._vazio is not None:
            self._vazio.destroy()
            self._vazio = None
        j = len(self.lista_ids_global)
        self.lista_ids_global.append(id_extraido)

        linha = ctk.CTkFrame(self.scroll, corner_radius=6, fg_color=COR["linha_alt"] if j % 2 else "transparent")
        linha.pack(fill="x", padx=(0, 8))
        ui.pill(linha, self.f, id_extraido, height=24, width=84).pack(side="left", padx=(8, 12), pady=6)
        ctk.CTkLabel(linha, text=f"{pags} pág{'s' if pags != 1 else ''}.", font=self.f["pequeno"],
                     text_color=COR["texto_sec"]).pack(side="right", padx=12)
        ctk.CTkLabel(linha, text=nome, font=self.f["mono"], text_color=COR["texto"], anchor="w").pack(
            side="left", fill="x", expand=True)


if __name__ == "__main__":
    app = ScannerApp()
    app.mainloop()
