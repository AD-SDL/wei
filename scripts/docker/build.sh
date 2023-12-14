#!/usr/bin/env bash

source "$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"/script_helper.sh

cd $project_path

docker build \
	-t ghcr.io/ad-sdl/${project_name}:${project_version} \
	-t ghcr.io/ad-sdl/${project_name}:dev \
	-t ghcr.io/ad-sdl/${project_name}:latest \
	.
