# Proc-Scanner

Recolhe os IDs dos PDFs de uma pasta com 1 ou 3+ páginas (o segundo pedaço do nome,
`6475791_1408534_label.pdf` -> `1408534`) e copia-os para o clipboard separados por ` OR `.

- **App:** https://nhmac.github.io/Proc-Scanner/ (Chrome ou Edge; pode ser instalada como app)
- **Repositório:** https://github.com/nhmac/Proc-Scanner (código-fonte no `main`; o site é gerado e publicado pelo GitHub Actions)
- **Versão atual:** web 1.4: os IDs também aparecem em grupos de até 400 caracteres e 23 IDs (`MAX_IDS_GRUPO`),
  cada um com o seu botão Copiar, porque a caixa de pesquisa do Explorador do Windows 10 não aceita
  textos muito compridos (`LIMITE_PESQUISA`, no `web/scanner.html` e no `main.py`). O "Copiar IDs"
  da sidebar continua a copiar tudo de uma vez

Os PDFs são lidos no browser e não são enviados para lado nenhum.

## Atualizar a app

O GitHub é a única fonte: funciona igual em qualquer PC ou no Claude Code na web.

1. `git pull` (sempre antes de começar).
2. Alterar `web/scanner.html` e subir o "Versão web".
3. Testar: `py build_pages.py` gera o site em `_site/` (abrir o `_site/index.html`).
4. Publicar: commit e `git push`. O GitHub Actions ("Publicar site") gera e publica o site em
   1-2 minutos; os PCs recebem a versão nova ao abrir a app com internet.

Só usa a biblioteca padrão do Python e o git.

## Pastas

| | |
|---|---|
| `web/` | Fonte do site: `scanner.html`, ícones PNG e pdf-lib 1.17.1 (`vendor/pdf-lib`, MIT), que conta as páginas |
| `.github/workflows/pages.yml` | Gera e publica o site a cada push ao `main` |
| `Inter/`, `icone.ico` | Fonte Inter (SIL OFL) e ícone, usados pelo site e pela versão Python |
| `pdf-testes/`, `Papel 25/` | PDFs de exemplo para testes (só nos PCs, fora do git) |
| `main.py`, `processamento_ui.py` | Versão Python original (referência da lógica) |

## Versão Python

Precisa do `customtkinter`, do `pypdf` e do `pyperclip`, num ambiente virtual:

```
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```
