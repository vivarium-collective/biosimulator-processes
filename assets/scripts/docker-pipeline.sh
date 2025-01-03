#!/bin/bash


version="$1"

run="$2"

if [ "${version}" == "" ]; then
  echo "You must pass the container version you wish to run as an argument to this script. Exiting."
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

./scripts/build-container.sh "${version}" \
  && ./scripts/release-container.sh "${version}" \

if [ "${run}" == "-r" ]; then
  ./scripts/run-container.sh "${version}"
fi
