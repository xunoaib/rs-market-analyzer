#!/usr/bin/env python3
'''
A simple example demonstrating use of the Runescape wiki price API
'''

import requests
import json

HTTP_HEADERS = {'User-Agent': 'Market Experimentation'}

resp = requests.get('https://prices.runescape.wiki/api/v1/osrs/latest',
                    headers=HTTP_HEADERS)
prices = resp.json()

# print(prices)
# print(prices.keys())
# print(json.dumps(prices, indent=2))

# download mappings for the first time. this section can be commented out once
# they've been downloaded for the first time
mappings = requests.get('https://prices.runescape.wiki/api/v1/osrs/mapping',
                        headers=HTTP_HEADERS).json()
with open('mappings.json', 'w') as f:
    json.dump(mappings, f, indent=2)

# load item mapping info (item names, buy limit, etc)
with open('mappings.json') as f:
    mappings = json.load(f)

# transform list of item mappings into a nice dict with item ids as keys
mappings = {str(row['id']): row for row in mappings}

# display item names and their corresponding price info
for itemid, price_info in prices['data'].items():
    if itemid in mappings:  # some items dont have a corresponding mapping
        info = mappings[itemid]
        print(info['name'], '=>', price_info)
