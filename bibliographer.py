import urllib.request
import tempfile
import subprocess

zbmath_author_IDs = "{'IDs':['muro.fernando', 'gonzalez-meneses.juan', 'flores.ramon-j', 'silvero.marithania', 'carmona-sanchez.v', 'cumplido.maria', 'manchon.pedro-m-g']}"
zbmath_bibtex_baseurl = 'https://zbmath.org/bibtexoutput/?q=ia%3A'
zbmath_api_baseurl = 'https://api.zbmath.org/v1/document/_structured_search?author%20code='

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

print(bibtex_to_csljson(get_bibtex_from_zbmath('muro.fernando')))