import urllib
import urllib.request

zbmath_author_IDs = '{"IDs":['muro.fernando', 'gonzalez-meneses.juan', 'flores.ramon-j', 'silvero.marithania', 'carmona-sanchez.v', 'cumplido.maria', 'manchon.pedro-m-g']}'
zbmath_bibtex_baseurl = 'https://zbmath.org/bibtexoutput/?q=ia%3A'
zbmath_api_baseurl = 'https://api.zbmath.org/v1/document/_structured_search?author%20code='

def get_bibtex():
    f = open("zbmath.bib", "w")
    f.write('{')
    for author in zbmath_author_IDs['IDs']:
        f.write('"'+author+'":')
        # the replacement {\'{\i}} -> í is done in order to avoid biblatex/biber errors
        data = urllib.request.urlopen(
            zbmath_bibtex_baseurl+author).read().decode('utf-8').replace("{\\'{\i}}", "í")
        f.write(data)
        f.write('\n\n')
        f.write('{')
    f.close()