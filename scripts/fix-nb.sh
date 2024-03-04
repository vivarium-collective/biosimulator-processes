#!/bin/bash

if poetry run python3 -c "from biosimulator_processes.utils import fix_notebooks_execution_count as fix_notebooks; fix_notebooks(); exit()"; then
  echo "Notebooks fixed!"
else
  echo "Notebooks not fixed."
fi
