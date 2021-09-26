 #This example uses Python 2.7 and the python-request library.

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import csv

url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
parameters = {
  'start':'1',
  'limit':'5000',
  'convert':'USD'
}
headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': '2461b386-5ba1-465f-ad5e-d8a58b3a3cac',
}

session = Session()
session.headers.update(headers)

try:
  response = session.get(url, params=parameters)
  data = json.loads(response.text)
except (ConnectionError, Timeout, TooManyRedirects) as e:
  print(e)

with open('person2.json', 'w') as json_file:
  json.dump(data, json_file)

# with open('crypto.csv', 'w', newline='') as file:
#     writer = csv.writer(file)
#     for row in data:
#         print(row)
#         writer.writerow(row) 