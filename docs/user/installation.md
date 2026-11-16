# Installation

nyx-bridge-blender is installed as a **Blender extension**: a zip holding the add-on and
the wheels of the Python packages it needs (this package and `nyx-bridge`), so nothing is
installed into Blender's own Python and nothing is downloaded when Blender installs it.

## Requirements

- Blender 4.2 or newer.
- [uv](https://docs.astral.sh/uv/), `make` and `git`, to build the extension from source.

## 1. Tell the build where Blender is

Create a `.env` file in the project root (or `~/.config/blender-ci.env`):

```sh
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
```

| Variable | Meaning |
| --- | --- |
| `BLENDER` | The Blender executable. Used to build the zip, validate the manifest and install. |

Typical locations:

| Platform | Executable |
| --- | --- |
| macOS | `/Applications/Blender.app/Contents/MacOS/Blender` |
| Windows | `C:\Program Files\Blender Foundation\Blender 4.2\blender.exe` |
| Linux | `/usr/bin/blender`, or where you unpacked Blender |

The file is looked up in this order: `BLENDER_CI_ENV_FILE`, `./.env`,
`~/.config/blender-ci.env`.

## 2. Install

```sh
make install
```

This runs two steps you can also run alone:

| Target | What it does |
| --- | --- |
| `make extension` | Builds `dist/nyx_bridge_blender-<version>.zip`: wheels of this package and of `sowwic-nyx-bridge` (at the version in `uv.lock`, downloaded from the package index) plus the extension, packed by Blender. |
| `make install` | Builds the zip, then installs it in the `user_default` repository and enables it. |

To remove it: `make uninstall`. `make validate` checks `extension/blender_manifest.toml`
with Blender.

### Without make

Build the zip with `make extension`, then in Blender use **Edit > Preferences > Get
Extensions**, the arrow menu (top right) and **Install from Disk**. Blender keeps
installed extensions in its user folder, for example
`~/Library/Application Support/Blender/<version>/extensions/user_default/`.

## 3. Check it in Blender

Open the 3D viewport sidebar (`N`): there is a **Nyx** tab. In the Python Console:

```python
import nyx_bridge_blender
print(nyx_bridge_blender.__version__)
```

The extension asks for the `network` permission ("Connect to Nyx on this computer"),
which Blender shows in the extension's entry.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `Set BLENDER in ...` | The env file is missing or does not define `BLENDER`. |
| `blender_manifest.toml is at version X, VERSION says Y` | Run `make update-version`. |
| `Not pure Python, so not bundled: ...` | A dependency in `uv.lock` only has platform specific wheels. One zip serves every platform, so only `py3-none-any` wheels can be bundled. |
| No **Nyx** tab in the sidebar | The extension is not enabled: Edit > Preferences > Add-ons. |
| `No module named nyx_bridge_blender` | Installed some other way than as the extension zip, which carries the wheels. |
| Old behavior after pulling changes | Run `make install` again. |
