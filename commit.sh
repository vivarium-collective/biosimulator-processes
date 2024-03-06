#!/bin/bash

branch="$1"

if [ "${branch}" == "" ]; then
  branch="main"
fi

echo "Enter commit message: "
read -r msg

# if poetry run python3 -c "from biosimulator_processes.utils import fix_notebooks_execution_count as fix_notebooks; fix_notebooks(); exit()"; then
#   echo "Notebooks fixed!"
# else
#   echo "Notebooks not fixed."
# fi

python3 ./scripts/fix_notebooks.py
git add --all
git commit -m "${msg}"
git push origin "${branch}"

