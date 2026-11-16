# Starting Blender from a stage

A stage can start a headless Blender itself, wait for it to connect and run its Remote
Actions in it. Use a **Launch Process** node around a **Remote Client**:

```text
Launch Process  ->  Remote Client  ->  Remote Action ...
```

Settings of the Launch Process node:

| Input | Value |
| --- | --- |
| `command` | `"$BLENDER" --background --python-exit-code 1 --python-expr "import nyx_bridge_blender; nyx_bridge_blender.serve_background()"` |
| `env` | `{"BLENDER": "/Applications/Blender.app/Contents/MacOS/Blender"}` |
| `timeout` | Seconds to wait for Blender to boot (default 60). |

Nyx gives the process the address and token of its bridge server and the name it is to
connect as (`NYX_BRIDGE_ADDRESS`, `NYX_BRIDGE_TOKEN`, `NYX_BRIDGE_CLIENT_NAME`), which
`serve_background` uses. The Remote Client inside the node uses that Blender and no other.

- The extension has to be [installed](installation.md): Blender loads it from the user
  preferences, so do not start with `--factory-startup`.
- `blender --background` has no event loop, so requests run on the calling thread and
  `serve_background` does not reconnect: it returns when Nyx asks Blender to shut down
  or the connection ends, and Blender exits as its script is done.
- `--python-exit-code 1` makes Blender's exit code say that the script failed.
- When the nodes inside are done Nyx asks Blender to shut down, and stops the process if
  it does not. The Nyx window waits while Blender boots.
- A small launcher script holding the command makes the node's `command` just its path.

## Without Nyx starting it

In your own `blender --background` script:

```python
from nyx_bridge_blender import BlenderClient

BlenderClient().serve_forever()     # blocks; address from the environment or address file
```

`serve_background(name, address, token, connect_timeout)` takes the same settings. Give
`connect_timeout` (seconds) to fail with `ConnectionError` instead of waiting forever.
