.PHONY: lint
lint:
	black .

.PHONY: lint-check
lint-check:
	black --check .