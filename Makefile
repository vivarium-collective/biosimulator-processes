.PHONY: docs help sync commit push

all: sync

commit:
	@git commit -m "$(m)"

push:
	@git push


docs:
	@uv run mkdocs serve

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

sync: 
	@uv sync --frozen --all-extras

.DEFAULT_GOAL := help