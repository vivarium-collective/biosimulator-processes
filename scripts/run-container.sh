#!/bin/bash

version="$1"

if [ "${version}" == "" ]; then
  echo "Please enter the version you would like to run as a runtime arg. Exiting."
  exit 1
fi

docker run --platform linux/amd64 -it -p 8888:8888 ghcr.io/biosimulators/biosimulator-processes:"${version}"
