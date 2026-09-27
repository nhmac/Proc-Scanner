# Proc-Scanner

Recolhe os IDs dos PDFs de uma pasta com 1 ou 3+ páginas (o segundo pedaço do nome,
`6475791_1408534_label.pdf` -> `1408534`) e copia-os para o clipboard separados por ` OR `.

**Abrir:** https://nhmac.github.io/Proc-Scanner/ (Chrome ou Edge; pode ser instalada como app:
ícone de instalar na barra de endereço).

Os PDFs são lidos no próprio browser e **não são enviados para lado nenhum**.

Este repositório é gerado: não editar aqui. A fonte é `web/scanner.html` na pasta
`Processamento_PDF Scanner` do projeto Processamento, e o site gera-se com `build_pages.py`.

Terceiros: [pdf-lib](https://github.com/Hopding/pdf-lib) (MIT, `vendor/pdf-lib/LICENSE.md`),
fonte [Inter](https://rsms.me/inter/) (SIL OFL 1.1, `fonts/OFL.txt`).
