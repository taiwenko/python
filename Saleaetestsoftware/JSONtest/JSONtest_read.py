__author__ = 'Logan Herrera'

import json
from pprint import pprint

with open('result.json') as data_file:
    data = json.load(data_file)

pprint(data)