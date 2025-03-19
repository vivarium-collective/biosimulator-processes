#!/usr/bin/env bash

# create base
conda clean --all -y
conda env create -f ./environment.yml -y

# create integrated poetry env
env_name=$(conda env list | grep '*' | awk '{print $1}')
conda update -n "$env_name" poetry -y
conda run -n "$env_name" poetry env use 3.10
conda run -n "$env_name" poetry install

# ./assets/scripts/install-smoldyn-mac-silicon.sh
