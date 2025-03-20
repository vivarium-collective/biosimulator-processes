#!/usr/bin/env bash

simulator="$1"
params="$2"

BASE_VENV=".venv"
TEMP_VENV="/tmp/temp_uv_venv"

uv venv $TEMP_VENV

ln -s "$(realpath $BASE_VENV/lib/python3.*/site-packages)" $TEMP_VENV/lib/python3.*/site-packages

ENV_BIN=$TEMP_VENV/bin

$ENV_BIN/uv pip install --extra "$simulator"

$ENV_BIN/python -c "import some_extra_package; print('Temporary env running successfully!')"

rm -rf $TEMP_VENV
