# User Guide

This guide is for people who connect Blender to Nyx.

## Pages

| Page | What you learn |
| --- | --- |
| [Installation](installation.md) | Building and installing the Blender extension, checking that Blender has it. |
| [Connecting Blender to Nyx](connecting.md) | The sidebar panel, the preferences, the Python API, addresses and tokens, what scripts see. |
| [Starting Blender from a stage](background.md) | Headless `blender --background` started by a Launch Process node. |

## How it fits together

```text
   Nyx                                       Blender
┌──────────────┐ Blender connects out   ┌───────────────────┐
│ BridgeServer │ ◀───────────────────── │ BlenderClient     │
│              │ ───── execute ───────▶ │ runs on the main  │
│ ClientSession│ ◀──── result ───────── │ thread            │
└──────────────┘                        └───────────────────┘
```

1. Nyx listens on a local port and holds a secret token.
2. Blender starts a `BlenderClient` (with the **Connect to Nyx** button or
   `nyx_bridge_blender.start()`), which keeps trying until Nyx accepts it.
3. Nyx sends code; Blender runs it on its main thread and answers with the value and the
   captured output.

Protocol and server details are in the
[nyx-bridge documentation](https://sowwic.github.io/nyx-bridge/).
