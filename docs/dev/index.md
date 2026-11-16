# Developer Guide

This guide is for people who work on nyx-bridge-blender itself.

## Setup

```bash
uv sync
make check        # ruff + pytest with bpy
make mkdocs       # serve these docs
```

`make help` lists every target. Ruff uses a line length of 89 and the `E`, `F` and `UP`
rules. Docstrings are Google style: the API reference is generated from them.

Tests do not need a Blender install: they use the `bpy` package. See
[Testing](testing.md).

!!! important
    `import nyx_bridge_blender` must work **outside Blender** (docs, tooling), so `bpy`,
    `bmesh` and `mathutils` are imported inside the methods that use them. Only the
    modules of `extension/` import `bpy` at the top, since Blender is the only one
    loading them.

## Pages

| Page | What you learn |
| --- | --- |
| [Architecture](architecture.md) | The package, the extension, threads and the main-thread pump. |
| [Testing](testing.md) | The `bpy` package, the test layout and CI. |
| [Releasing](releasing.md) | Versions, the changelog and `make release`. |
| API reference | Generated from the docstrings (see the navigation). |
