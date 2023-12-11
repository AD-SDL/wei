#!/bin/bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

echo `grep -oP '(?<=name = ")[^"]+' $SCRIPTPATH/../../pyproject.toml | head -n 1`
