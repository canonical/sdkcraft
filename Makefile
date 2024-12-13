.PHONY: clean
clean: ## Clean artefacts from building, testing, etc.
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf .tox/
	rm -f .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache
	rm -rf .mypy_cache

.PHONY: dist
dist: clean ## Build python package.
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

.PHONY: lint
lint: test-codespell test-ruff test-mypy test-yamllint test-shellcheck test-pyright ## Run all linting tests.
	
.PHONY: test-codespell
test-codespell:
	codespell . --summary --count --ignore-words-list="buildd,create,keyserver,commandos,ro,dedent,dedented"

.PHONY: test-ruff
test-ruff:
	ruff check sdkcraft tests

.PHONY: test-mypy
test-mypy:
	mypy --install-types --non-interactive sdkcraft

.PHONY: test-pyright
test-pyright:
	pyright sdkcraft tests 

.PHONY: test-yamllint
test-yamllint:
	yamllint . 

.PHONY: test-shellcheck
test-shellcheck:
	# shellcheck for shell scripts
	git ls-files | file --mime-type -Nnf- | grep shellscript | cut -f1 -d: | xargs shellcheck

.PHONY: test-units
test-units: ## Run unit tests.
	pytest tests/unit

.PHONY: test-integrations
test-integrations: ## Run integration tests.
	pytest tests/integration

.PHONY: install
install: clean ## Install python package.
	python setup.py install

.PHONY: spread
spread: ## Build a fresh snap and run spread tests
	rm -f tests/*.snap
	snapcraft clean
	snapcraft -o tests
	spread
