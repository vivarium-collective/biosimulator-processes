#!/usr/bin/env bash

module_name="$1"
hosted_flag="${2:---hosted}"

MODULE_LOCATION="$(realpath backend/$module_name)"
HOSTED_MODULE="github.com/vivarium-collective/biosimulator-processes/backend/$module_name"

if [ "$hosted_flag" == "--hosted" ]; then
    (
        cd "$MODULE_LOCATION" || exit 1
        go mod tidy
        go mod vendor
        echo "Successfully packaged Go module location: $MODULE_LOCATION as a hosted module: $HOSTED_MODULE"
    )
fi 