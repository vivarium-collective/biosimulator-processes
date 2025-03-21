#!/usr/bin/env bash
set -e

cd backend || return 

for d in gateway server proto shared; do
  echo "Tidying module: $d"
  (cd $d && go mod tidy)
done
