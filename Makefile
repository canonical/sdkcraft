PROJECT=sdkcraft
UV_TEST_GROUPS := "--group=dev"
UV_DOCS_GROUPS := "--group=dev"
UV_LINT_GROUPS := "--group=dev"
UV_TICS_GROUPS := "--group=dev"

ifneq ($(wildcard /etc/os-release),)
include /etc/os-release
endif
ifdef VERSION_CODENAME
UV_TEST_GROUPS += "--group=dev-$(VERSION_CODENAME)"
UV_DOCS_GROUPS += "--group=dev-$(VERSION_CODENAME)"
UV_LINT_GROUPS += "--group=dev-$(VERSION_CODENAME)"
UV_TICS_GROUPS += "--group=dev-$(VERSION_CODENAME)"
endif

include common.mk

.PHONY: format
format: format-ruff format-codespell format-prettier format-pre-commit  ## Run all automatic formatters

.PHONY: lint
lint: lint-ruff lint-codespell lint-mypy lint-prettier lint-pyright lint-shellcheck lint-twine lint-uv-lockfile  ## Run all linters

.PHONY: test-units
test-units:  ## Run unit tests
	uv run pytest tests/unit

.PHONY: test-integrations
test-integrations:  ## Run integration tests
	uv run pytest tests/integration

.PHONY: pack
pack: pack-pip  ## Build all packages

.PHONY: pack-snap
pack-snap: snap/snapcraft.yaml  ##- Build snap package
ifeq ($(shell which snapcraft),)
	sudo snap install --classic snapcraft
endif
	snapcraft pack

# Find dependencies that need installing
APT_PACKAGES :=
ifeq ($(wildcard /usr/include/libxml2/libxml/xpath.h),)
APT_PACKAGES += libxml2-dev
endif
ifeq ($(wildcard /usr/include/libxslt/xslt.h),)
APT_PACKAGES += libxslt1-dev
endif
ifeq ($(wildcard /usr/share/doc/python3-venv/copyright),)
APT_PACKAGES += python3-venv
endif

# Used for installing build dependencies in CI.
.PHONY: install-build-deps
install-build-deps: install-lint-build-deps
ifeq ($(APT_PACKAGES),)
else ifeq ($(shell which apt-get),)
	$(warning Cannot install build dependencies without apt.)
	$(warning Please ensure the equivalents to these packages are installed: $(APT_PACKAGES))
else
	sudo $(APT) install $(APT_PACKAGES)
endif

# If additional build dependencies need installing in order to build the linting env.
.PHONY: install-lint-build-deps
install-lint-build-deps:
