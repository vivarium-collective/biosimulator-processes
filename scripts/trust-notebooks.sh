#!/bin/bash

# Trust all notebooks in a specific directory
find /app/notebooks -name "*.ipynb" -exec jupyter trust {} \;
