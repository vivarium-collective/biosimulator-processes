#!/bin/bash


version="$1"

# PLEASE UPDATE THE LATEST VERSION HERE BEFORE RUNNING. CURRENT: 0.0.4
current="0.0.4"

if [ "${version}" == "" ]; then
  echo "You must pass the container version you wish to release as an argument to this script. Exiting."
  exit 1
fi

if [ "${version}" == "${current}" ]; then
  echo "This version already exists on GHCR. Exiting."
  exit 1
fi

echo "Enter your Github User-Name: "
read -r usr_name

if docker login ghcr.io -u "${usr_name}"; then
  echo "Successfully logged in to GHCR!"
else
  echo "Could not validate credentials."
  exit 1
fi

yes | docker system prune && yes | docker buildx prune
docker push ghcr.io/vivarium-collective/biosimulator-processes:"${version}"
docker tag ghcr.io/vivarium-collective/biosimulator-processes:"${version}" ghcr.io/vivarium-collective/biosimulator-processes:latest
docker push ghcr.io/vivarium-collective/biosimulator-processes:latest
