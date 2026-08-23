import re
import urllib.parse
import urllib.request
import feedparser
import json
import yaml

atom = 'https://arxiv.org/a/'
BibTeX = 'https://arxiv.org/bibtex/'
RSS = "http://export.arxiv.org/api/query?"

# This function retrieves from arXiv the JSON feed of the publications of a given author ORCID
def get_JSON_from_arXiv(ORCID):
    return feedparser.parse(atom+ORCID+'.atom2')

# This function retrieves from arXiv the YAML feed of the publications of a given author ORCID
def get_YAML_from_arXiv(ORCID):
    data = get_JSON_from_arXiv(ORCID)
    return yaml.dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)

# This function retrieves from arXiv the RSS feed of the publications of a given author name
def get_search_output_from_string(author):
    return urllib.request.urlopen(RSS+"search_query=au:"+author).read().decode('utf-8')


def get_paper_JSON_from_arXiv(arxiv_id: str):
    """Fetch the arXiv feed JSON for a single paper identifier."""
    normalized = normalize_arxiv_id(arxiv_id)
    if not normalized:
        raise ValueError(f"Invalid arXiv identifier: {arxiv_id}")

    return feedparser.parse(RSS+"id_list="+arxiv_id)

def get_paper_YAML_from_arXiv(arxiv_id: str):
    """Fetch the arXiv feed YAML for a single paper identifier."""
    data = get_paper_JSON_from_arXiv(arxiv_id)
    return yaml.dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)

def extract_arxiv_summary(json_arxiv, arxiv_ID):
    for entry in json_arxiv['entries']:
        if arxiv_ID in entry['id']:
            return entry['summary']

def extract_published_date(json_arxiv, arxiv_ID):
    for entry in json_arxiv['entries']:
        if arxiv_ID in entry['id']:
            return entry['published']

def normalize_arxiv_id(arxiv_id: str) -> str:
    normalized = arxiv_id.strip()
    normalized = re.sub(r"(?i)^doi:\s*", "", normalized)
    normalized = re.sub(r"(?i)^https?://doi\.org/", "", normalized)
    normalized = re.sub(r"(?i)^https?://arxiv\.org/(abs|pdf)/", "", normalized)
    normalized = re.sub(r"(?i)^arxiv:\s*", "", normalized)

    doi_match = re.match(r"(?i)^10\.48550/arxiv\.([\w\.\-/]+)$", normalized)
    if doi_match:
        normalized = doi_match.group(1)

    return normalized


def get_paper_bibtex_from_arxiv(arxiv_id: str) -> str:
    """
    Fetch BibTeX for an arXiv identifier from arXiv's entry bibtex endpoint.

    The function accepts identifiers like '1304.6641', 'math/0603544',
    'arXiv:1304.6641', or DOI-style values such as
    '10.48550/arXiv.2107.14174'.
    """
    normalized = normalize_arxiv_id(arxiv_id)
    if not normalized:
        raise ValueError(f"Invalid arXiv identifier: {arxiv_id}")

    url = f"{BibTeX}{urllib.parse.quote(normalized)}"

    try:
        return urllib.request.urlopen(url).read().decode('utf-8')
    except Exception as exc:
        raise RuntimeError(f"arXiv bibtex retrieval failed for {arxiv_id}: {exc}") from exc

