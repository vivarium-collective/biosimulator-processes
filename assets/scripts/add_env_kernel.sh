#!/usr/bin/env bash

env="$1"
python_version=$(poetry run python --version)
poetry run python -m ipykernel install --user --name="$env" --display-name "Biosimulator Processes($env): $python_version"
