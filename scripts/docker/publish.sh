#!/usr/bin/env bash

source "$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"/script_helper.sh

$scripts_path/build.sh

docker push ghcr.io/ad-sdl/${project_name}:${project_version}
