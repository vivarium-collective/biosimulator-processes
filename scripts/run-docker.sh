#!/bin/bash


version="$1"

# PLEASE UPDATE THE LATEST VERSION HERE BEFORE RUNNING. CURRENT: 0.0.2
current="0.0.2"

if [ "${version}" == "" ]; then
  echo "You must pass the container version you wish to run as an argument to this script. Exiting."
  exit 1
fi

echo "Push container to GHCR after building? (y/N): "
read -r push

echo "Run container after building? (y/N): "
read -r run_after

if [ "${push}" == 'y' ]; then
  echo "Enter your Github User-Name: "
  read -r usr_name

  if docker login ghcr.io -u "${usr_name}"; then
    echo "Successfully logged in to GHCR!"
  else
    echo "Could not validate credentials."
    exit 1
  fi
fi

yes | docker system prune
docker buildx create --name biosimbuilder --use
docker buildx inspect --bootstrap

if [ "${push}" == 'y' ]; then
  if [ "${version}" == "${current}" ]; then
    echo "This version already exists on GHCR. Exiting."
    exit 1
  fi
  docker buildx build --platform linux/amd64 \
    -t ghcr.io/biosimulators/biosimulator-processes:"${version}" . \
    --push
  docker tag ghcr.io/biosimulators/biosimulator-processes:"${version}" ghcr.io/biosimulators/biosimulator-processes:latest
  docker push ghcr.io/biosimulators/biosimulator-processes:latest
else
  docker buildx build --platform linux/amd64 -t ghcr.io/biosimulators/biosimulator-processes:"${version}" .
fi


if [ "${run_after}" == 'y' ]; then
  docker run --platform linux/amd64 -it -p 8888:8888 ghcr.io/biosimulators/biosimulator-processes:"${version}"
fi
