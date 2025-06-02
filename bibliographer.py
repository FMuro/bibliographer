#!.venv/bin/python3
import libbibliographer
import yaml
import json

data = libbibliographer.merged_data_dict('muro.fernando','0000-0001-8457-9889')
with open('output.yml', 'w') as outfile:
    yaml.dump(data, outfile, default_flow_style=False)
with open("output.json", "w") as outfile: 
    json.dump(data, outfile)