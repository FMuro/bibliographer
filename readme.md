This project contains:

- `zbmathbibtex.py` script to download all zbMATH records of a list of authors in a single `.bib` file called `zbmath.bib`.
- `arxivbibtex.py` script to download all arXiv records of an author in a single `.bib` file called `arxiv.bib`. The code is just a simplification of [this script by Sven-S. Porst](https://github.com/ssp/arXivToBibTeX/blob/master/lookup.py).
- `biber.tex` prints the previous `.bib` file.
- `zbmath.py` is a minimal example reading the zbMATH API.
- `arxiv.py` is a minimal example reading the arXiv API.
- `arxivatom.py` tries to read an atom feed from arXiv.