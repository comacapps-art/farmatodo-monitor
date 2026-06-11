import re
html = open('search_page.html', encoding='utf-8').read()
pages = re.findall(r'href=[^\s>]+page=\d+', html)
print("Pages:", pages)
print("Pagination tags:", re.findall(r'<li[^>]*pagination[^>]*>.*?</li>', html, re.IGNORECASE))
