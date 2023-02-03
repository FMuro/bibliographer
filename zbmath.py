import urllib
import urllib.request
import xmltodict
url = 'https://oai.zbmath.org/v1/helper/filter?filter=author_id%3Amuro.fernando&metadataPrefix=oai_zb_preview'
data = urllib.request.urlopen(url)
dict = xmltodict.parse(data.read().decode('utf-8'))
# print(data.read().decode('utf-8'))
print((((dict['OAI-PMH'])['ListRecords'])['record'])[0])
