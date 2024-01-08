#!/bin/bash

# This is a helper script for active development

git add --all \
  && echo "enter your commit message: " \
  && read -r msg \
  && git commit -m "$msg" && git push
