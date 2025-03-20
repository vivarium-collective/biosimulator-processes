#!/usr/bin/env bash

original_img_name="$1"
version="$2"
org="$3"
default_org="vivarium-collective"

if [ "$org" == "" ]; then
  org=$default_org
fi

img_prefix="ghcr.io/$org"

docker tag "$original_img_name" "$img_prefix/$original_img_name:$version"

