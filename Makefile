.PHONY: docs help sync 

all: sync 

docs:
	@uv run mkdocs serve

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

sync: 
	@uv sync --frozen --all-extras

.DEFAULT_GOAL := help