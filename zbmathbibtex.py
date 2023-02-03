import urllib
import urllib.request
baseurl = 'https://zbmath.org/bibtexoutput/?q=ia%3A'
authors = ['muro.fernando', 'gonzalez-meneses.juan']
f = open("zbmath.bib", "w")
for author in authors:
    # the replacement {\'{\i}} -> í is done in order to avoid biblatex/biber errors
    data = urllib.request.urlopen(
        baseurl+author).read().decode('utf-8').replace("{\\'{\i}}", "í")
    f.write(data)
    f.write('\n\n')
f.close()
