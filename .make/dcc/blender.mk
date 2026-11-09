# Blender extension: build the zip with the wheels of the package, install it through Blender.
#
# Needs PACKAGE_NAME and general/python. BLENDER (the executable) comes from an env file:
# BLENDER_CI_ENV_FILE, then ./.env, then ~/.config/blender-ci.env.
# Set LINT_PATHS = src tests extension scripts and
# PYTEST_CMD = uv run --group bpy pytest tests (the bpy package is the Blender the tests use).

ENV_FILE ?= $(or $(BLENDER_CI_ENV_FILE),$(wildcard .env),$(HOME)/.config/blender-ci.env)
EXTENSION_ID ?= $(PACKAGE_NAME)
EXTENSION_USER_REPO ?= user_default

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
