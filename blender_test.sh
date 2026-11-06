#!/usr/bin/env bash
set -euo pipefail

# Runs the test suite inside Blender (`blender --background`), with the package and
# the test dependencies installed for the Python Blender ships. Extra arguments are
# passed to pytest. The tests folder is always run: do not pass it again.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -n "${BLENDER_CI_ENV_FILE:-}" ]]; then
  ENV_FILE="$BLENDER_CI_ENV_FILE"
elif [[ -f "$ROOT_DIR/.env" ]]; then
  ENV_FILE="$ROOT_DIR/.env"
else
  ENV_FILE="$HOME/.config/blender-ci.env"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Blender test configuration was not found."
  echo "Expected one of:"
  echo "  $ROOT_DIR/.env"
  echo "  $HOME/.config/blender-ci.env"
  echo "Or set BLENDER_CI_ENV_FILE to an explicit file path."
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

if [ -z "${BLENDER:-}" ]; then
  echo "BLENDER not set. Define it in $ENV_FILE"
  exit 1
fi

echo "Using Blender: $BLENDER"

SITE_DIR="$ROOT_DIR/build/blender_pytest/site"
rm -rf "$ROOT_DIR/build/blender_pytest"
mkdir -p "$SITE_DIR"

BLENDER_PYTHON="$("$BLENDER" --background --factory-startup \
  --python-expr 'import sys; print("PYTHON_EXECUTABLE=" + sys.executable)' |
  sed -n 's/^PYTHON_EXECUTABLE=//p')"

echo "Installing the package and test dependencies for $BLENDER_PYTHON"
uv pip install \
  --python "$BLENDER_PYTHON" \
  --target "$SITE_DIR" \
  --group blender-pytest \
  "$ROOT_DIR"

NYX_TEST_SITE="$SITE_DIR" "$BLENDER" --background --factory-startup \
  --python-exit-code 1 \
  --python "$ROOT_DIR/tests/run_pytest.py" -- -vvv "$ROOT_DIR/tests" "$@"
