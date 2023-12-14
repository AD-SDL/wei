#!/usr/bin/env bash

# Invoke this helper from other scripts in the scripts dir of a project with:
# source "$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"/script_helper.sh

USER_ID=$(id -u)
GROUP_ID=$(id -g)

scripts_path="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $scripts_path
project_path=`git rev-parse --show-toplevel`
if [[ -f ${project_path}/pyproject.toml ]]; then
	project_name=`grep -oP '(?<=name = ")[^"]+' $project_path/pyproject.toml | head -n 1`
	project_version=`grep -oP '(?<=version = ")[^"]+' $project_path/pyproject.toml | head -n 1`
else
	project_name=`basename $project_path`
	project_version="0.0.0"
fi
