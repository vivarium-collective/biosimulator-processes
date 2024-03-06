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
  --platform linux/amd64 \
  -t ghcr.io/vivarium-collective/biosimulator-processes:"${version}" .

docker push ghcr.io/vivarium-collective/biosimulator-processes:"${version}"
docker tag ghcr.io/vivarium-collective/biosimulator-processes:"${version}" ghcr.io/vivarium-collective/biosimulator-processes:latest
docker push ghcr.io/vivarium-collective/biosimulator-processes:latest

if [ "${run}" == "-r" ]; then
  ./scripts/run-container.sh "${version}"
fi
