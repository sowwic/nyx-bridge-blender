"""Run pytest inside Blender.

    NYX_TEST_SITE=<site folder> blender -b --python tests/run_pytest.py -- <args>

Blender's Python ignores PYTHONPATH, so the folder holding the installed package and
pytest is given in `NYX_TEST_SITE`.
"""

import os
import sys

site = os.environ.get("NYX_TEST_SITE")
if site:
    sys.path.insert(0, site)

import pytest  # noqa: E402

arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
sys.exit(pytest.main(arguments))
