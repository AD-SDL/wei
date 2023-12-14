#!/usr/bin/env bash

source "$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"/script_helper.sh
cd $project_path

docker compose down
