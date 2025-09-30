import urllib.request
import tempfile
import subprocess
import feedparser
import json
import re


opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'MyApp/1.0')]
urllib.request.install_opener(opener)

zbmath_bibtex_baseurl = 'https://zbmath.org/bibtexoutput/?q=ia%3A'
zbmath_entry_bibtex_baseurl = 'https://zbmath.org/bibtex/'
zbmath_api_baseurl = 'https://api.zbmath.org/v1/document/_search?search_string=ia%3A'
arxiv_atom_baseurl = 'https://arxiv.org/a/'
arxiv_entry_bibtex_baseurl = 'https://arxiv.org/bibtex/'

# This function retrieves the bibtex of the publications of a given zbmath author ID
def get_bibtex_from_zbmath(zbmath_author_ID):
    # the replacement {\'{\i}} -> í is done in order to avoid biblatex/biber errors
    return urllib.request.urlopen(
            zbmath_bibtex_baseurl+zbmath_author_ID).read().decode('utf-8').replace("{\\'{\\i}}", "í")

def get_bibtex_from_arxiv(arxiv_ID):
    # the replacement {\'{\i}} -> í is done in order to avoid biblatex/biber errors
    return urllib.request.urlopen(
            arxiv_entry_bibtex_baseurl+arxiv_ID).read().decode('utf-8').replace("{\\'{\\i}}", "í")

# This function converts a bibtex string to a CSL JSON string
# It uses pandoc to do the conversion
def bibtex_to_csljson(bibtex):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(bibtex)
        f.close()
        return subprocess.check_output(['pandoc', '-f', 'bibtex', f.name, '-t', 'csljson']).decode('utf-8')

# This function retrieves the JSON of the publications of a given zbmath author ID
def get_json_from_zbmath(zbmath_author_ID):
    return json.loads(urllib.request.urlopen(
            zbmath_api_baseurl+zbmath_author_ID).read().decode('utf-8'))

# This function retrieves from arXiv the JSON feed of the publications of a given author ORCID
def get_dict_from_arxiv(orcid):
    return feedparser.parse(arxiv_atom_baseurl+orcid+'.atom2')

# create dictionary with paper's zbmath_id : { 'zbmath_url' : zbmath_url, 'arxiv' : arxiv_ID } the latter only if available
def get_extra_zbmath_data(json_zbmath):
    extra_zbmath_data_dict = {}
    for entry in json_zbmath["result"]:
        if entry["database"] == "arXiv":
            key = entry["identifier"]
        else:
            key = entry["id"]
        entry_data = {}
        entry_data["zbmath_url"] = entry["zbmath_url"]
        for link in entry["links"]:
            if link["type"] == "arxiv":
                entry_data["arxiv"] = link["identifier"]
        extra_zbmath_data_dict[key] = entry_data
    return extra_zbmath_data_dict

# create dictionary with paper's arxiv_id : { 'abstract': abstract }
def get_extra_arxiv_data(dict_arxiv):
    extra_arxiv_data_dict = {}
    for entry in dict_arxiv["entries"]:
        entry_data = {}
        entry_data["abstract"] = str(entry["summary_detail"]["value"])
        extra_arxiv_data_dict[re.sub('v[0-9]+', '', entry["id"].replace("http://arxiv.org/abs/",""))] = entry_data
    return extra_arxiv_data_dict

# list of arXiv IDs of papers in zbmath bibtex
def arxiv_in_bibtex_zbmath(bibtex_zbmath):
    list_arxiv = []
    for line in bibtex_zbmath.splitlines():
        if line.startswith('@misc{arXiv:'):
            list_arxiv.append(re.sub('v[0-9]+', '', line.replace("@misc{arXiv:","").replace(",","")))
    return list_arxiv

# list of arXiv IDs of papers in zbmath CSL JSON
def arxiv_in_csl_json_zbmath(csl_json_zbmath):
    list_arxiv = []
    for entry in csl_json_zbmath:
        if "arXiv" in entry["id"]:
            list_arxiv.append(entry["id"].replace("arXiv:",""))
    return list_arxiv

# list of arXiv IDs of papers in zbmath JSON
def arxiv_in_json_zbmath(json_zbmath):
    list_arxiv = []
    for entry in json_zbmath["result"]:
        for link in entry["links"]:
            if link["type"] == "arxiv":
                list_arxiv.append(link["identifier"])
    return list_arxiv

# list of arXiv IDs of papers in dictionary obtained from arXiv's Atom feed
def arxiv_in_dict_arxiv(dict_arxiv):
    list_arxiv = []
    for entry in dict_arxiv["entries"]:
        list_arxiv.append(re.sub('v[0-9]+', '', entry["id"].replace("http://arxiv.org/abs/","")))
    return list_arxiv

# take zbMATH bibtex and add arXiv bibtex of papers in arXiv Atom feed after lower bound year but not in zbMATH bibtex
def bibtex(bibtex_zbmath, json_zbmath, dict_arxiv, lower_bound_year=0):
    in_bibtex_zbmath = arxiv_in_bibtex_zbmath(bibtex_zbmath)
    in_json_zbmath = arxiv_in_json_zbmath(json_zbmath)
    in_zbmath = in_bibtex_zbmath + in_json_zbmath
    in_dict_arxiv = arxiv_in_dict_arxiv(dict_arxiv)
    difference = [entry for entry in in_dict_arxiv if entry not in in_zbmath]
    for entry in difference:
        bibtex_arxiv = get_bibtex_from_arxiv(entry)
        year = re.search(r'year=\{(\d{4})\}', bibtex_arxiv).group(1)
        primaryclass = re.sub(r'\.(.*)', r'.{\1}', re.search(r'primaryClass=\{(.*?)\}', bibtex_arxiv).group(1))
        if int(year) > lower_bound_year:
            bibtex_zbmath = re.sub(r'^\}$', '      howpublished={Preprint, {arXiv}:' + entry + ' [' + primaryclass + '] (' + year + ')}\n}', re.sub(r'@misc\{(.*?)\,', '@misc{arXiv:' + entry + ',', bibtex_arxiv), flags=re.MULTILINE) + "\n\n" + bibtex_zbmath
    # Replace title = {...} with title = {{...}}, handling cases with or without spaces around '='
    bibtex_zbmath = re.sub(
        r'(title\s*=\s*)\{(.*)\}',
        lambda m: f"{m.group(1)}{{{{{m.group(2)}}}}}",
        bibtex_zbmath
    )
    return bibtex_zbmath

# take bibtex from zbmath, turn it into dict, add extra data from zbmath and arxiv and also { 'bibtex' : bibtex_entry }
def merged_data_dict(bibtex_string,csl_json,json_zbmath,dict_arxiv):
    bibtex_split = bibtex_string.split('\n\n')
    extra_zbmath_data = get_extra_zbmath_data(json_zbmath)
    extra_arxiv_data = get_extra_arxiv_data(dict_arxiv)
    for idx, entry in enumerate(csl_json):
        # bibtex after stripping down non-standard entries
        entry["bibtex"] = re.sub(r'primaryClass=.*\n', '', re.sub(r'archivePrefix=.*\n', '', re.sub(r'eprint=.*\n', '', re.sub(r'arXiv =.*\n', '', re.sub(r'zbMATH =.*\n', '', re.sub(r'Zbl =.*\n', '', bibtex_split[idx]))))))
        if "zbMATH" in entry["id"]:
            try:
                entry.update(extra_zbmath_data[int(entry["id"].strip('zbMATH'))])
            except:
                pass
            try:
                entry.update(extra_arxiv_data[entry["arxiv"]])
            except:
                pass
        else: 
            try:
                entry.update(extra_arxiv_data[entry["id"].replace("arXiv:","")])
            except:
                pass
            try:
                entry["arxiv"] = re.sub('v[0-9]+', '', entry["id"].replace("arXiv:",""))
            except:
                pass
    return csl_json