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

    resource_id = "01J3KPJSY5FMHBWRQCS8MNXVN3"  # Replace with an actual resource ID
    asset = Asset(name="TEST_PLATE")
    response = requests.post(
        f"{BASE_URL}/resources/{resource_id}/push", json=asset.model_dump()
    )
    print(f"POST /resources/{resource_id}/push")
    print(response.json())


def test_pop_resource():
    """"""
    resource_id = "01J3KPJSY5FMHBWRQCS8MNXVN3"  # Replace with an actual resource ID
    response = requests.post(f"{BASE_URL}/resources/{resource_id}/pop")
    print(f"POST /resources/{resource_id}/pop")
    print(response.json())


def test_increase_pool():
    """"""
    plate_id = "01J3KPJSYA3BSYCNDDXW5D36SW"  # Replace with an actual plate ID
    pool_id = "01J3KPJSY6KR9F15XYRJXPGHSN"  # Replace with an actual pool ID
    amount = 20.0  # Adjust the amount to be increased
    response = requests.post(
        f"{BASE_URL}/resources/{plate_id}/pools/{pool_id}/increase",
        params={"amount": amount},
    )
    print(f"POST /resources/{plate_id}/pools/{pool_id}/increase")
    print(response.json())


def test_decrease_pool():
    """"""
    plate_id = "01J3EJ9DJ14025FAJR74QGGCQ3"  # Replace with an actual plate ID
    pool_id = "01J3EJ9DHWT29H423DKPJGWMDK"  # Replace with an actual pool ID
    amount = 10.0  # Adjust the amount to be decreased
    response = requests.post(
        f"{BASE_URL}/resources/{plate_id}/pools/{pool_id}/decrease",
        params={"amount": amount},
    )
    print(f"POST /resources/{plate_id}/pools/{pool_id}/decrease")
    print(response.json())


def test_fill_pool():
    """"""
    plate_id = "01J3EJ9DJ14025FAJR74QGGCQ3"  # Replace with an actual plate ID
    pool_id = "01J3EJ9DHWT29H423DKPJGWMDK"  # Replace with an actual pool ID
    response = requests.post(f"{BASE_URL}/resources/{plate_id}/pools/{pool_id}/fill")
    print(f"POST /resources/{plate_id}/pools/{pool_id}/fill")
    print(response.json())


def test_empty_pool():
    """"""
    plate_id = "01J3EJ9DJ14025FAJR74QGGCQ3"  # Replace with an actual plate ID
    pool_id = "01J3EJ9DHWT29H423DKPJGWMDK"  # Replace with an actual pool ID
    response = requests.post(f"{BASE_URL}/resources/{plate_id}/pools/{pool_id}/empty")
    print(f"POST /resources/{plate_id}/pools/{pool_id}/empty")
    print(response.json())


def test_update_plate():
    """"""
    plate_id = "01J3EJ9DJ14025FAJR74QGGCQ3"  # Replace with an actual plate ID
    new_contents = {"A1": 10.0, "A2": 20.0}  # Adjust the contents as needed
    response = requests.put(
        f"{BASE_URL}/resources/{plate_id}/update_plate", json=new_contents
    )
    print(f"PUT /resources/{plate_id}/update_plate")
    print(response.json())


def test_insert_collection():
    """"""
    collection_id = "01J3HKP4EX03BB3KJDQHS6GF3T"  # Replace with an actual collection ID
    location = "A1"  # Location to insert the asset
    asset = Asset(name="TEST_ASSET")
    response = requests.post(
        f"{BASE_URL}/resources/{collection_id}/insert",
        json={"location": location, "asset": asset.model_dump()},
    )
    print(f"POST /resources/{collection_id}/insert")
    print(response.json())


def test_retrieve_collection():
    """"""
    collection_id = "01J3HKP4EX03BB3KJDQHS6GF3T"  # Replace with an actual collection ID
    location = "A1"  # Location to retrieve the asset from
    response = requests.post(
        f"{BASE_URL}/resources/{collection_id}/retrieve", json={"location": location}
    )
    print(f"POST /resources/{collection_id}/retrieve")
    print(response.json())


def test_save_resources():
    """"""
    response = requests.post(f"{BASE_URL}/resources/save")
    print("POST /resources/save")
    print(response.json())


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
    test_push_resource()
    test_increase_pool()
