# nyx-bridge-blender

![Tests](https://github.com/sowwic/nyx-bridge-blender/actions/workflows/unit_tests.yml/badge.svg)
![Code Quality](https://github.com/sowwic/nyx-bridge-blender/actions/workflows/code_quality.yml/badge.svg)

Connects Blender to a running [Nyx](https://github.com/sowwic/nyx), so stages can send
commands to Blender and get results back. Blender connects out to Nyx's bridge server;
Nyx never launches or reaches into Blender on its own.

## Install

The client is a Blender **extension** (Blender 4.2 or newer): a zip holding the add-on
and the Python packages it needs, so nothing else has to be installed.

```sh
make install       # build dist/nyx_bridge_blender-<version>.zip and install it, enabled
make uninstall     # disable and remove it
```

`make install` needs `BLENDER` (path of the Blender executable) in a `.env` file in the
project root, or in `~/.config/blender-ci.env`:

```sh
BLENDER=/path/to/Blender.app/Contents/MacOS/Blender
```

Without make: build the zip with `make extension`, then in Blender use
Edit > Preferences > Get Extensions > the arrow menu (top right) > Install from Disk.
Blender keeps installed extensions in its user folder, for example
`~/Library/Application Support/Blender/<version>/extensions/user_default/`.

## Use

With Nyx running, open the 3D viewport sidebar (`N`), tab **Nyx**, and press
**Connect to Nyx**. Nyx is found through the address file it writes, so on the same
machine no setup is needed. Otherwise give the address and token in Edit > Preferences >
Add-ons > Nyx Bridge, where **Connect on start** is also found.

Blender then shows up in Nyx's Bridge panel as a client of kind `blender`, and the
Remote Client and Remote Action nodes can use it. What Nyx sends runs on Blender's main
thread, and scripts find `bpy`, `bmesh` and `mathutils` in their namespace.

From Python in Blender:

```python
import nyx_bridge_blender

nyx_bridge_blender.start()                 # background thread, returns the client
nyx_bridge_blender.is_connected()
nyx_bridge_blender.stop()
```

In `blender --background` there is no event loop to hand work to, so serve from the
main thread instead: `nyx_bridge_blender.BlenderClient().serve_forever()`.

## Development

```sh
uv sync            # install the project and dev dependencies
make check         # lint + tests
make help          # list all targets
```

The tests run with the [`bpy`](https://pypi.org/project/bpy/) package, Blender as a
Python module, so no Blender install is needed (a 250 MB download the first time).
`bpy` 5.2 needs Python 3.13, see `.python-version`. `make pytest` runs them, and CI does
the same.

A plain `pytest` without `bpy` skips everything that needs Blender. `make validate` checks the
extension manifest.

## Releasing

1. Add a `v<version>` entry to `CHANGELOG.rst`, update `VERSION` (`make update-version`) and commit on `main`.
2. `make release VERSION=<version>` tags, pushes (triggering the GitHub release workflow) and back-merges into `develop`.
