#!/bin/bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

version=`$SCRIPTPATH/version.sh`
name=`$SCRIPTPATH/name.sh`

docker push ghcr.io/ad-sdl/${name}:${version}
