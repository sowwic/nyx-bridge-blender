# Common targets come from sowwic/makefiles, fetched into .make/ (commit it). `make update-make` fetches them again.
APP_NAME = nyx-bridge-blender
PACKAGE_NAME = nyx_bridge_blender
LINT_PATHS = src tests extension scripts
PYTEST_CMD = uv run --group bpy pytest tests
PYTEST_PDB_CMD = uv run --group bpy pytest -vvv --pdb --log-cli-level=DEBUG tests

MAKEFILES_REF ?= v1
MAKEFILES_URL ?= https://raw.githubusercontent.com/sowwic/makefiles/$(MAKEFILES_REF)
MAKEFILES_MODULES = general/python dcc/blender

.make/%.mk:
	@mkdir -p $(dir $@)
	@curl -fsSL $(MAKEFILES_URL)/$*.mk -o $@
include $(MAKEFILES_MODULES:%=.make/%.mk)
