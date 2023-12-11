#!/bin/bash

export USER_ID=`id -u`
export GROUP_ID=`id -g`

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

cd $SCRIPTPATH/../..

docker compose restart
