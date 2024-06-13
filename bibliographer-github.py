#!./bin/python3
from libbibliographer import get_bibtex_from_zbmath

data = merged_data_dict('muro.fernando','0000-0001-8457-9889')
with open('output.bib', 'w') as outfile:
    outfile.write(get_bibtex_from_zbmath('muro.fernando'))