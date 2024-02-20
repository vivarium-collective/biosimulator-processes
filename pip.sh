#!/bin/bash

pkg="$1"

pip install "${pkg}"
pip show "${pkg}"

