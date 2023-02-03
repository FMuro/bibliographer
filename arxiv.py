import urllib
import urllib.request
url = "http://export.arxiv.org/api/query?search_query=au:'muro+f'"
data = urllib.request.urlopen(url)
print(data.read().decode('utf-8'))
