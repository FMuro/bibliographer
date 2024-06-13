#!./bin/python3
from libbibliographer import get_bibtex_from_zbmath

with open('output.bib', 'w') as outfile:
    outfile.write(get_bibtex_from_zbmath('muro.fernando'))