import os
import json
import csv
from helpers import lookup
import time

if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

f = open('iexsymbols.json')

data = json.load(f)

# for x in range(20):
#     symbol = (data[x]['symbol'])
#     price = lookup(str(symbol))
#     #price = price['price']
#     print(symbol, price['price'])

# with open('egg.csv', 'w', newline='') as file:
#     writer = csv.writer(file)
#     for row in data:
#         writer.writerow([row['symbol'], row['name']])
start_time = time.time()
out = []

for x in range(10):
    symbol = (data[x]['symbol'])
    price = lookup(str(symbol))
    if price == None:
        price = 0
    else:
        price = price['price']
    name = (data[x]['name'])
    out.append({'symbol':symbol, 'name':name, 'price':price})
    print(symbol, name, price)

print('++++++++++++++')
for row in out:
    print(row)

print("--- %s seconds ---" % (time.time() - start_time))