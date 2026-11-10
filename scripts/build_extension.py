#!/usr/bin/env python3
"""Build the Blender extension zip.

Blender installs an extension without fetching anything, so the zip carries the wheels
of this package and of its dependencies. The dependencies are built from the git
revisions pinned in `[tool.uv.sources]` of `pyproject.toml`.

    BLENDER=/path/to/Blender python scripts/build_extension.py [--output-dir dist]
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXTENSION_DIR = ROOT / "extension"
BUILD_DIR = ROOT / "build"
WHEELS_MARKER = "# The wheels are added by `scripts/build_extension.py`."


def run(*command: str | os.PathLike, cwd: pathlib.Path | None = None) -> None:
    """Run a command, stopping the build when it fails."""
    subprocess.run([str(part) for part in command], cwd=cwd, check=True)


def dependency_name(requirement: str) -> str:
    """Get the project name of a requirement like `nyx-bridge>=1`."""
    return re.split(r"[<>=!~\[; ]", requirement.strip(), maxsplit=1)[0]


def build_dependency_wheel(name: str, source: dict, wheels_dir: pathlib.Path) -> None:
    """Build the wheel of a dependency from the git revision it is pinned to.

    Args:
        name (str): project name.
        source (dict): its entry of `[tool.uv.sources]`, a git url with a rev or tag.
        wheels_dir (pathlib.Path): folder to put the wheel in.
    """
    if "git" not in source:
        raise SystemExit(f"Cannot bundle {name}: it has no git source in pyproject.toml")
    reference = source.get("rev") or source.get("tag") or source.get("branch")
    checkout = BUILD_DIR / "dependencies" / name
    shutil.rmtree(checkout, ignore_errors=True)
    run("git", "clone", "--quiet", source["git"], checkout)
    if reference:
        run("git", "checkout", "--quiet", reference, cwd=checkout)
    run("uv", "build", "--wheel", "--out-dir", wheels_dir, checkout)


def write_manifest(source_dir: pathlib.Path, wheel_names: list[str]) -> None:
    """Put the wheels into the manifest of the extension being built.

    Args:
        source_dir (pathlib.Path): folder of the extension, holds the manifest.
        wheel_names (list[str]): file names of the wheels in its `wheels` folder.
    """
    manifest = source_dir / "blender_manifest.toml"
    text = manifest.read_text(encoding="utf-8")
    version = tomllib.loads(text)["version"]
    expected = (ROOT / "VERSION").read_text().strip()
    if version != expected:
        raise SystemExit(
            f"blender_manifest.toml is at version {version}, VERSION says {expected}"
        )
    wheels = ",\n".join(f'  "./wheels/{name}"' for name in wheel_names)
    if WHEELS_MARKER not in text:
        raise SystemExit("blender_manifest.toml lost the line marking where wheels go")
    manifest.write_text(
        text.replace(WHEELS_MARKER, f"wheels = [\n{wheels},\n]"), encoding="utf-8"
    )


def main() -> None:
    """Assemble the extension and let Blender build the zip."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--blender", default=os.environ.get("BLENDER"))
    parser.add_argument("--output-dir", type=pathlib.Path, default=ROOT / "dist")
    args = parser.parse_args()
    if not args.blender:
        raise SystemExit("Set BLENDER to the Blender executable, or pass --blender")

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    sources = pyproject.get("tool", {}).get("uv", {}).get("sources", {})

    source_dir = BUILD_DIR / "extension"
    shutil.rmtree(source_dir, ignore_errors=True)
    shutil.copytree(
        EXTENSION_DIR, source_dir, ignore=shutil.ignore_patterns("__pycache__", "wheels")
    )
    wheels_dir = source_dir / "wheels"
    wheels_dir.mkdir()

    run("uv", "build", "--wheel", "--out-dir", wheels_dir, ROOT)
    for requirement in pyproject["project"].get("dependencies", []):
        name = dependency_name(requirement)
        build_dependency_wheel(name, sources.get(name, {}), wheels_dir)

    write_manifest(source_dir, sorted(path.name for path in wheels_dir.glob("*.whl")))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    run(
        args.blender,
        "--command",
        "extension",
        "build",
        "--source-dir",
        source_dir,
        "--output-dir",
        args.output_dir,
    )


if __name__ == "__main__":
    sys.exit(main())
