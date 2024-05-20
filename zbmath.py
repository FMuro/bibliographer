import urllib
import urllib.request
import xmltodict
import json
url = 'https://api.zbmath.org/v1/document/_structured_search?page=0&results_per_page=100&author%20code=muro.fernando'
data = urllib.request.urlopen(url)
dict = json.loads(data.read().decode('utf-8'))
# dict = xmltodict.parse(data.read().decode('utf-8'))
# print(data.read().decode('utf-8'))
for item in dict['result']:
    print(item['title']['title'])
