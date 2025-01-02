#!/bin/bash

version="$1"

run="$2"

if [ "${version}" == "" ]; then
  echo "Please enter the version you would like to build as a runtime arg. Exiting."
  exit 1
fi

yes | docker system prune && yes | docker buildx prune
# docker buildx create --name biosimbuilder --use
docker buildx create --name vivariumBuilder --use
docker buildx inspect --bootstrap

set -e

docker build \
  --no-cache \
  --platform linux/amd64 \
  -t ghcr.io/vivarium-collective/biosimulator-processes:"${version}" .

if [ "${run}" == "-r" ]; then
  ./scripts/run-container.sh "${version}"
fi
