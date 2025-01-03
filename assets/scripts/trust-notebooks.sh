#!/bin/bash

# Trust all composer-notebooks in a specific directory
find /app/notebooks -name "*.ipynb" -exec jupyter trust {} \;
