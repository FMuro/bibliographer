import feedparser
url = "https://arxiv.org/a/0000-0001-8457-9889.atom2"
feed = feedparser.parse(url)
print(feed)
