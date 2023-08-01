from album import *
from search import *

import requests

# resp = requests.get('http://vgmdb.net/album/114566')
# if resp.status_code != 200:
#     raise Exception('Failed to fetch page')
# html = resp.text
# a = parse_page(html)
# print(a)


fetch_page('4540774242023')