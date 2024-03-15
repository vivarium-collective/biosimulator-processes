#!/bin/bash

branch="$1"

if [ "${branch}" == "" ]; then
  echo "Please specify a branch..."
  read -r branch
  if [ "${branch}" == "" ]; then
    branch="main"
  fi
fi

echo "Enter commit message: "
read -r msg

python3 ./scripts/fix_notebooks.py
git add --all
git commit -m "${msg}"
git push origin "${branch}"

