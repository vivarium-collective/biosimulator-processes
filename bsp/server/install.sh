#!/usr/bin/env bash

editable=${1:-""}

root_path=$(python -c "import bsp; import os; print(os.path.dirname(os.path.dirname(bsp.__file__)))")
uv pip install -e "$root_path""[cobra,copasi,dev,docs,membrane,quantum,vcell]"