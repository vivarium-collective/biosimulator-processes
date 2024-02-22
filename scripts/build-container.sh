#!/bin/bash

version="$1"

set -e

if [ "${version}" == "" ]; then
  echo "Please enter the version you would like to build as a runtime arg. Exiting."
  exit 1
fi

yes | docker system prune
docker buildx create --name biosimbuilder --use
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64 \
    -t ghcr.io/biosimulators/biosimulator-processes:"${version}" .
