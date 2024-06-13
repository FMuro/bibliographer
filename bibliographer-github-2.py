from libbibliographer import merged_data_dict_github

data = merged_data_dict_github('muro.fernando','middle.json',0000-0001-8457-9889')
with open('output.yml', 'w') as outfile:
    yaml.dump(data, outfile, default_flow_style=False)
with open("output.json", "w") as outfile: 
    json.dump(data, outfile)