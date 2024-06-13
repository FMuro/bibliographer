import urllib.request
import tempfile
import subprocess
import feedparser
import json
import re
import yaml

zbmath_bibtex_baseurl = 'https://zbmath.org/bibtexoutput/?q=ia%3A'
zbmath_entry_bibtex_baseurl = 'https://zbmath.org/bibtex/'
zbmath_api_baseurl = 'https://api.zbmath.org/v1/document/_structured_search?author%20code='
arxiv_atom_baseurl = 'https://arxiv.org/a/'
arxiv_entry_bibtex_baseurl = 'https://arxiv.org/bibtex/'

# This function retrieves the bibtex of the publications of a given zbmath author ID
def get_bibtex_from_zbmath(zbmath_author_ID):
    # the replacement {\'{\i}} -> í is done in order to avoid biblatex/biber errors
    return urllib.request.urlopen(
            zbmath_bibtex_baseurl+zbmath_author_ID).read().decode('utf-8').replace("{\\'{\\i}}", "í")

# This function converts a bibtex string to a CSL JSON string
# It uses pandoc to do the conversion
def bibtex_to_csljson(bibtex):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(bibtex)
        f.close()
        return subprocess.check_output(['pandoc', '-f', 'bibtex', f.name, '-t', 'csljson']).decode('utf-8')

# This function retrieves the JSON of the publications of a given zbmath author ID
def get_json_from_zbmath(zbmath_author_ID):
    return urllib.request.urlopen(
            zbmath_api_baseurl+zbmath_author_ID).read().decode('utf-8')

# This function retrieves from arXiv the JSON feed of the publications of a given author ORCID
def get_dict_from_arxiv(orcid):
    return feedparser.parse(arxiv_atom_baseurl+orcid+'.atom2')

# create dictionary with paper's zbmath_id : { 'zbmath_url' : zbmath_url, 'arxiv' : arxiv_ID } the latter only if available
def get_extra_zbmath_data(zbmath_author_ID):
    source = json.loads(get_json_from_zbmath(zbmath_author_ID))
    extra_zbmath_data_dict = {}
    for entry in source["result"]:
        entry_data = {}
        entry_data["zbmath_url"] = entry["zbmath_url"]
        for link in entry["links"]:
            if link["type"] == "arxiv":
                entry_data["arxiv"] = link["identifier"]
        extra_zbmath_data_dict[entry["id"]] = entry_data
    return extra_zbmath_data_dict

# create dictionary with paper's arxiv_id : { 'abstract': abstract }
def get_extra_arxiv_data(orcid):
    source = get_dict_from_arxiv(orcid)
    extra_arxiv_data_dict = {}
    for entry in source["entries"]:
        entry_data = {}
        entry_data["abstract"] = str(entry["summary_detail"]["value"])
        extra_arxiv_data_dict[re.sub('v[0-9]+', '', entry["id"].replace("http://arxiv.org/abs/",""))] = entry_data
    return extra_arxiv_data_dict

# take bibtex from zbmath, turn it into dict, add extra data from zbmath and arxiv and also { 'bibtex' : bibtex_entry }
def merged_data_dict(zbmath_author_ID, orcid):
    bibtex = get_bibtex_from_zbmath(zbmath_author_ID)
    bibtex_split = bibtex.split('\n\n')
    data = json.loads(bibtex_to_csljson(bibtex))
    extra_zbmath_data = get_extra_zbmath_data(zbmath_author_ID)
    extra_arxiv_data = get_extra_arxiv_data(orcid)
    for idx, entry in enumerate(data):
        entry_extra_zbmath_data = extra_zbmath_data[int(entry["id"].strip('zbMATH'))]
        # bibtex after stripping down non-standard entriesfil
        entry["bibtex"] = re.sub('arXiv =.*\n', '', re.sub('zbMATH =.*\n', '', re.sub('Zbl =.*\n', '', bibtex_split[idx])))
        entry.update(entry_extra_zbmath_data)
        if "arxiv" in entry_extra_zbmath_data.keys():
            entry.update(extra_arxiv_data[entry_extra_zbmath_data["arxiv"]])
    return data
    
# take bibtex from zbmath, turn it into dict, add extra data from zbmath and arxiv and also { 'bibtex' : bibtex_entry }
def merged_data_dict_github(zbmath_author_ID, bibfile, orcid):
    bibtex = get_bibtex_from_zbmath(zbmath_author_ID)
    bibtex_split = bibtex.split('\n\n')
    data = json.loads(bibfile)
    extra_zbmath_data = get_extra_zbmath_data(zbmath_author_ID)
    extra_arxiv_data = get_extra_arxiv_data(orcid)
    for idx, entry in enumerate(data):
        entry_extra_zbmath_data = extra_zbmath_data[int(entry["id"].strip('zbMATH'))]
        # bibtex after stripping down non-standard entriesfil
        entry["bibtex"] = re.sub('arXiv =.*\n', '', re.sub('zbMATH =.*\n', '', re.sub('Zbl =.*\n', '', bibtex_split[idx])))
        entry.update(entry_extra_zbmath_data)
        if "arxiv" in entry_extra_zbmath_data.keys():
            entry.update(extra_arxiv_data[entry_extra_zbmath_data["arxiv"]])
    return data