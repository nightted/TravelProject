from googlesearch import search
from webpreview import web_preview

query = "文章牛肉湯"
urls = []

for url in search(query, stop=5, pause=2.0):
	urls.append(url)

for url in urls:
  print(web_preview(url))