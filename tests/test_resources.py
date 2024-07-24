"""Test resource endpoint"""

import requests

from wei.types.resource_types import Asset

BASE_URL = (
    "http://localhost:2001"  # Adjust this to match your server's address if different
)


def test_get_state():
    """"""
    response = requests.get(f"{BASE_URL}/state")
    print("GET /state")
    print(response.json())


def test_get_resources():
    """"""

    response = requests.get(f"{BASE_URL}/resources")
    print("GET /resources")
    print(response.json())


def test_push_resource():
    """"""

    resource_id = "01J3HKP4EX03BB3KJDQHS6GF3T"  # Replace with an actual resource ID
    asset = Asset(name="TEST_PLATE")
    response = requests.post(
        f"{BASE_URL}/resources/{resource_id}/push", json=asset.model_dump()
    )
    print(f"POST /resources/{resource_id}/push")
    print(response.json())


def test_pop_resource():
    """"""

    resource_id = "Stack1"  # Replace with an actual resource ID
    response = requests.post(f"{BASE_URL}/resources/{resource_id}/pop")
    print(f"POST /resources/{resource_id}/pop")
    print(response.json())


def test_increase_pool():
    """"""

    resource_id = "Plate1"  # Replace with an actual resource ID
    well_id = "A1"  # Replace with an actual well ID
    amount = {"amount": 10}
    response = requests.post(
        f"{BASE_URL}/resources/{resource_id}/wells/{well_id}/increase", json=amount
    )
    print(f"POST /resources/{resource_id}/wells/{well_id}/increase")
    print(response.json())


def test_decrease_pool():
    """"""
    resource_id = "Plate1"  # Replace with an actual resource ID
    well_id = "A1"  # Replace with an actual well ID
    amount = {"amount": 5}
    response = requests.post(
        f"{BASE_URL}/resources/{resource_id}/wells/{well_id}/decrease", json=amount
    )
    print(f"POST /resources/{resource_id}/wells/{well_id}/decrease")
    print(response.json())


def test_write_resources():
    """"""
    response = requests.post(f"{BASE_URL}/resources/write")
    print("POST /resources/write")
    print(response.json())


# if __name__ == "__main__":
#     test_get_state()
#     test_get_resources()
#     test_push_resource()
#     test_pop_resource()
#     test_increase_pool()
#     test_decrease_pool()
#     test_write_resources()


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
    # test_push_resource()
    # test_increase_pool()
