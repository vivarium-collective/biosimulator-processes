#!/usr/bin/env bash

env=$(conda env list | grep '*' | awk '{print $1}')
python_version=$(conda run -n "$env" python --version)
conda run -n "$env" python -m ipykernel install --user --name="$env" --display-name "bsp($env): $python_version"
