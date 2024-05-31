#!./bin/python3
import urllib.request
import tempfile
import subprocess
import feedparser
import json
import re
import yaml
import sys

zbmath_author_IDs = "{'IDs':['muro.fernando', 'gonzalez-meneses.juan', 'flores.ramon-j', 'silvero.marithania', 'carmona-sanchez.v', 'cumplido.maria', 'manchon.pedro-m-g']}"
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

# create dictionary with paper's zbmath_id : { 'zbmath_url' : zbmath_url, 'bibtex' : bibtex_entry, 'arxiv' : arxiv_ID } the latter only if available
def get_extra_zbmath_data(zbmath_author_ID):
    source = json.loads(get_json_from_zbmath(zbmath_author_ID))
    extra_zbmath_data_dict = {}
    for entry in source["result"]:
        entry_data = {}
        entry_data["zbmath_url"] = entry["zbmath_url"]
        # get bibtex entry as string
        #
        # entry_identifier = entry['identifier']
        # if not entry_identifier:
        #     entry_data["bibtex"] = urllib.request.urlopen(
        #         zbmath_entry_bibtex_baseurl+str(entry['id']).zfill(8)+'.bib').read().decode('utf-8')
        # elif 'arXiv' in entry_identifier:
        #     print(arxiv_entry_bibtex_baseurl+entry_identifier)
        #     entry_data["bibtex"] = urllib.request.urlopen(
        #     arxiv_entry_bibtex_baseurl+entry_identifier).read().decode('utf-8')
        # else:
        #     entry_data["bibtex"] = urllib.request.urlopen(
        #         zbmath_entry_bibtex_baseurl+entry_identifier+'.bib').read().decode('utf-8')
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
        entry_data["abstract"] = entry["summary_detail"]["value"]
        extra_arxiv_data_dict[re.sub('v[0-9]+', '', entry["id"].replace("http://arxiv.org/abs/",""))] = entry_data
    return extra_arxiv_data_dict

# take bibtex from zbmath, turn it into dict, add keys { 'arxiv', 'zbmath_url', 'zbl', 'abstract' }, the two last ones when arxiv is available
def merged_data_dict(zbmath_author_ID, orcid):
    data = json.loads(bibtex_to_csljson(get_bibtex_from_zbmath(zbmath_author_ID)))
    extra_zbmath_data = get_extra_zbmath_data(zbmath_author_ID)
    extra_arxiv_data = get_extra_arxiv_data(orcid)
    for entry in data:
        entry_extra_zbmath_data = extra_zbmath_data[int(entry["id"].strip('zbMATH'))]
        entry.update(entry_extra_zbmath_data)
        if "arxiv" in entry_extra_zbmath_data.keys():
            entry.update(extra_arxiv_data[entry_extra_zbmath_data["arxiv"]])
    return data

with open('data.yml', 'w') as outfile:
    yaml.dump(merged_data_dict('muro.fernando','0000-0001-8457-9889'), outfile, default_flow_style=False)

# print(get_json_from_zbmath('muro.fernando'))