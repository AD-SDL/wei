"""Precursor to the experiment module."""
import json
from argparse import ArgumentParser
from pathlib import Path

import requests


def put_job(host="127.0.0.1", port="8000"):
    url = f"http://{host}:{port}/job/?simulate=True"

    yaml_file = Path(__file__).parent / "../tests/test_dummy_workflow.yaml"
    json_payload = {"data": {"key": "value"}}

    with open(yaml_file, "rb") as f:
        response = requests.post(
            url,
            files={"workflow": (str(yaml_file), f, "application/x-yaml")},
            data={"payload": json.dumps(json_payload)},
        )

    print(f"Status:\t{response.status_code}\nJSON:\t{response.json()}")


def query_job(job_id, host="127.0.0.1", port="8000"):
    url = f"http://{host}:{port}/job/{job_id}"
    response = requests.get(url)
    print(response.json())


def query_queue(host="127.0.0.1", port="8000"):
    url = f"http://{host}:{port}/queue/info"
    response = requests.get(url)
    print(response.json())


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--put-job", action="store_true")
    parser.add_argument("--query-job", type=str)
    parser.add_argument("--query-queue", action="store_true")

    args = parser.parse_args()

    if args.put_job:
        put_job()

    if args.query_job:
        query_job(args.query_job)

    if args.query_queue:
        query_queue()
