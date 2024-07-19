"""Test resource endpoint"""

import requests


def get_resources():
    """Get resources"""
    url = "http://localhost:2001/resources"
    response = requests.get(url)
    if response.status_code == 200:
        resources = response.json()
        print("Resources:", resources)
    else:
        print(f"Failed to get resources: {response.status_code}")


if __name__ == "__main__":
    get_resources()
