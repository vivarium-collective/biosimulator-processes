#!/bin/bash

version="$1"

if [ "${version}" == "" ]; then
  echo "Please enter the version you would like to run as a runtime arg. Exiting."
  exit 1
fi

docker exec \
  -it biosimulator-processes-container \
  sh -c "poetry run jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root"
