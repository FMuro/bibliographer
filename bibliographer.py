#!.venv/bin/python3
from libbibliographer import merged_data_dict, get_bibtex_from_zbmath, get_json_from_zbmath, get_dict_from_arxiv, bibtex, bibtex_to_csljson
import yaml
import json

bibtex_zbmath = get_bibtex_from_zbmath('muro.fernando')
json_zbmath = get_json_from_zbmath('muro.fernando')
dict_arxiv = get_dict_from_arxiv('0000-0001-8457-9889')
bibtex_string = bibtex(bibtex_zbmath, dict_arxiv, 2020)
csl_json = json.loads(bibtex_to_csljson(bibtex_string))

data = merged_data_dict(bibtex_string, csl_json, json_zbmath, dict_arxiv)

with open('output.yml', 'w') as outfile:
    yaml.dump(data, outfile, default_flow_style=False)
with open("output.json", "w") as outfile: 
    json.dump(data, outfile)