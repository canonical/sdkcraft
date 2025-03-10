PROJECT=sdkcraft
UV_TEST_GROUPS := "--group=dev"
UV_DOCS_GROUPS := "--group=dev"
UV_LINT_GROUPS := "--group=dev"

ifneq ($(wildcard /etc/os-release),)
include /etc/os-release
endif
ifdef VERSION_CODENAME
UV_TEST_GROUPS += "--group=dev-$(VERSION_CODENAME)"
UV_DOCS_GROUPS += "--group=dev-$(VERSION_CODENAME)"
UV_LINT_GROUPS += "--group=dev-$(VERSION_CODENAME)"
endif

include common.mk

.PHONY: format
format: format-ruff format-codespell  ## Run all automatic formatters

.PHONY: lint
lint: lint-ruff lint-codespell lint-mypy lint-pyright lint-shellcheck lint-twine lint-yamllint  ## Run all linters

.PHONY: lint-yamllint
lint-yamllint:  ##- Lint YAML files
ifneq ($(CI),)
	@echo ::group::$@
endif
	uv run yamllint .
ifneq ($(CI),)
	@echo ::endgroup::
endif

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
ifeq ($(wildcard /usr/share/doc/libapt-pkg-dev/copyright),)
APT_PACKAGES += libapt-pkg-dev
endif
ifeq ($(wildcard /usr/share/doc/libgit2-dev/copyright),)
APT_PACKAGES += libgit2-dev
endif
ifeq ($(wildcard /usr/share/doc/fuse-overlayfs/copyright),)
APT_PACKAGES += fuse-overlayfs
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
