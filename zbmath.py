#!/opt/homebrew/bin/python3

import urllib.request

# This retrieves the zbMATH Open publications of several authors
# authors zbMATH IDS
authors = ['muro.fernando', 'gonzalez-meneses.juan', 'flores.ramon-j', 'silvero.marithania', 'carmona-sanchez.v', 'cumplido.maria', 'manchon.pedro-m-g']
# zbMATH Open API base URL to get the publications of an author
baseurl = 'https://api.zbmath.org/v1/document/_structured_search?page=0&results_per_page=100&author%20code='
f = open("zbmath.json", "w")
for author in authors:
    data = urllib.request.urlopen(
        baseurl+author).read().decode('utf-8')
    f.write(data)
    f.write('\n\n')
f.close()
