#!/usr/bin/env python

"""Gets the state of the workcell from the WEI server."""

import json
from argparse import ArgumentParser

import requests

parser = ArgumentParser()
parser.add_argument("--server", type=str, help="Server IP address", default="localhost")
parser.add_argument("--port", type=str, help="Server port", default="8000")

args = parser.parse_args()

url = f"http://{args.server}:{args.port}/wc/state"

response = requests.get(url)

print(json.dumps(response.json(), indent=2))
