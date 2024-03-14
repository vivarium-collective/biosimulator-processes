#!/bin/bash


pip install -e git+https://github.com/vivarium-collective/bigraph-schema.git@experimental-pydantic#egg=bigraph_schema
pip install -e git+https://github.com/vivarium-collective/process-bigraph.git@main#egg=process_bigraph
pip install -e git+https://github.com/vivarium-collective/bigraph-viz.git@main#egg=bigraph_viz
pip install -e git+https://github.com/vivarium-collective/bigraph-builder.git@pydantic#egg=bigraph-builder
pip install -e .
