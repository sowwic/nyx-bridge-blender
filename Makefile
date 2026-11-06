SHELL := /bin/bash

APP_NAME = nyx-bridge-blender
PACKAGE_NAME = nyx_bridge_blender
VERSION := $(shell tr -d '\r\n' < VERSION)
DIST_DIR = dist
BUILD_DIR = build
MKDOCS_SITE_DIR = site
TEST_OUTPUT_DIR = .test_output
RELEASE_BRANCH ?= main
DEVELOP_BRANCH ?= develop
GH_WORKFLOWS_REF ?= v1
EXTENSION_ID = nyx_bridge_blender
EXTENSION_USER_REPO = user_default
# Same lookup as blender_test.sh: explicit file, project .env, then the user config
ENV_FILE ?= $(or $(BLENDER_CI_ENV_FILE),$(wildcard .env),$(HOME)/.config/blender-ci.env)

# Colors
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
MAGENTA := \033[35m
CYAN := \033[36m
RESET := \033[0m

# Banner helper
define banner
	@printf "$(CYAN)==>$(RESET) $(1)\n"
endef

.PHONY: help
help: ## Show this help message
	@echo "Available make targets:"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS=":.*?##"}; {printf "  %-15s %s\n", $$1, $$2}'
	@echo ""

.PHONY: clean
clean: ## Remove build artifacts, cache, and temporary files
	$(call banner, Cleaning project...)
	@rm -rf .pytest_cache
	@rm -rf .ruff_cache
	@rm -rf __pycache__
	@rm -rf .coverage
	@rm -rf src/**/__pycache__
	@rm -rf tests/**/__pycache__
	@rm -rf $(BUILD_DIR)
	@rm -rf $(DIST_DIR)
	@rm -rf $(TEST_OUTPUT_DIR)
	@rm -rf $(MKDOCS_SITE_DIR)
	@printf "$(GREEN)Clean up complete.$(RESET)\n"

.PHONY: lint
lint: ## Run the Ruff linter on source and test files
	$(call banner, Running Ruff linter...)
	@uv run ruff check src tests

.PHONY: lint-fix
lint-fix: ## Run the Ruff linter on source and test files and apply fixes
	$(call banner, Running Ruff linter with fixes...)
	@uv run ruff check --fix src tests

.PHONY: format
format: ## Run the Ruff formatter on source and test files
	$(call banner, Running Ruff formatter...)
	@uv run ruff format src tests

.PHONY: pytest
pytest: ## Run the tests inside Blender (BLENDER from the env file)
	$(call banner, Running pytest in Blender...)
	@./blender_test.sh

.PHONY: pytest-pdb
pytest-pdb: ## Run pytest with pdb on failure
	$(call banner, Cleaning pytest output dir...)
	@rm -rf $(TEST_OUTPUT_DIR)
	$(call banner, Running pytest with pdb...)
	@./blender_test.sh --pdb --log-cli-level=DEBUG

.PHONY: mkdocs
mkdocs: ## Run MkDocs development server
	$(call banner, Starting MkDocs development server...)
	@uv run mkdocs serve

.PHONY: check
check: lint pytest ## Run all checks (linting and testing)

.PHONY: build
build: ## Build the package using uv
	$(call banner, Building $(APP_NAME)...)
	@uv build

.PHONY: update-version
update-version: ## Update the version in pyproject.toml to match the VERSION file
	$(call banner, Updating version in pyproject.toml...)
	@printf "$(CYAN)==>$(RESET) Updating pyproject.toml version to %s\n" "$(VERSION)"
	@uv version $(VERSION)

.PHONY: release
release: ## Tag, push and back-merge a release: make release VERSION=x.y.z [RELEASE_TITLE=...]
	$(if $(VERSION),,$(error VERSION is required, e.g. make release VERSION=1.2.3))
	$(call banner, Releasing $(APP_NAME) v$(VERSION)...)
	@curl -fsSL https://raw.githubusercontent.com/sowwic/gh-workflows/$(GH_WORKFLOWS_REF)/scripts/release.py | \
		python3 - $(VERSION) --release-branch $(RELEASE_BRANCH) --develop-branch $(DEVELOP_BRANCH) $(if $(RELEASE_TITLE),--title "$(RELEASE_TITLE)")

.PHONY: extension
extension: ## Build the Blender extension zip into dist/
	$(call banner, Building the Blender extension...)
	@set -a; . "$(ENV_FILE)"; set +a; uv run python scripts/build_extension.py

.PHONY: validate
validate: ## Check the extension manifest with Blender
	@set -a; . "$(ENV_FILE)"; set +a; : "$${BLENDER:?Set BLENDER in $(ENV_FILE)}"; \
	"$$BLENDER" --command extension validate extension

.PHONY: install
install: extension ## Build the extension and install it in Blender, enabled
	@set -a; . "$(ENV_FILE)"; set +a; : "$${BLENDER:?Set BLENDER in $(ENV_FILE)}"; \
	"$$BLENDER" --command extension install-file -r $(EXTENSION_USER_REPO) --enable \
		$(DIST_DIR)/$(EXTENSION_ID)-$(VERSION).zip

.PHONY: uninstall
uninstall: ## Disable and remove the extension from Blender
	@set -a; . "$(ENV_FILE)"; set +a; : "$${BLENDER:?Set BLENDER in $(ENV_FILE)}"; \
	"$$BLENDER" --command extension remove $(EXTENSION_ID)
