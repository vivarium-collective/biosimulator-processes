#!/usr/bin/env bash

set -e

function gotidy() {
  workdir="$1"
  cd $workdir   
  files="$(python3 -c 'import os; print(os.path.abspath("."))')"
  
}
cd backend || return 

for d in gateway server proto shared; do
  echo "Tidying module: $d"
  (cd $d && go mod tidy)
done
