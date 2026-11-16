# Connecting Blender to Nyx

Once the extension is [installed](installation.md), Blender connects to Nyx in one of
three ways. All of them start a `BlenderClient`, which keeps retrying until Nyx is
running, and connects again if the connection drops.

## The sidebar panel

In the 3D viewport sidebar (`N`), tab **Nyx**:

| State shown | Meaning |
| --- | --- |
| Not connected | No client. Press **Connect to Nyx**. |
| Waiting for Nyx... | The client runs and keeps trying. **Disconnect from Nyx** stops it. |
| Connected to *server* | Nyx accepted Blender, shown with the name it uses. |

The panel redraws once a second, so it follows the connection by itself. Disabling the
extension disconnects.

## Preferences

**Edit > Preferences > Add-ons > Nyx Bridge**:

| Setting | Meaning |
| --- | --- |
| Connect on start | Connect when Blender starts or the extension is enabled (after a second, once the preferences are loaded). Off by default. |
| Address | `host:port` of Nyx. Empty finds a Nyx running on this computer. |
| Token | Token of the Nyx server. Empty uses the one Nyx wrote or the environment. |
| Name | Name Nyx shows for this Blender. Empty uses the process id. |

The button and **Connect on start** use these settings.

## From Python

Without the panel:

```python
import nyx_bridge_blender

nyx_bridge_blender.start()                      # background thread, returns the client
nyx_bridge_blender.is_running()                 # serving, connected or not
nyx_bridge_blender.is_connected()
nyx_bridge_blender.get_client()                 # the BlenderClient, None if not started
nyx_bridge_blender.stop()
```

`start(address=None, token=None, name=None)` returns the already running client if there
is one and ignores its arguments then. Call it from Blender's main thread.

## Finding Nyx

Blender looks for the host, port and token in this order:

1. The `address` and `token` arguments (the **Address** and **Token** preferences).
2. The environment: `NYX_BRIDGE_ADDRESS` (`host:port`) with `NYX_BRIDGE_TOKEN`.
3. The address file a running Nyx writes.

On the same machine nothing needs to be configured. For Nyx on another machine give
`host:port` and the token. Details are in
[Finding the server](https://sowwic.github.io/nyx-bridge/user/addresses/).

Blender then shows up in Nyx's Bridge panel as a client of kind `blender`, and the Remote
Client and Remote Action nodes can use it.

## What scripts see

What Nyx sends runs on **Blender's main thread**, so `bpy` is safe to use. The namespace
of a connection lives as long as the connection, and starts with:

| Name | Is |
| --- | --- |
| `bpy` | `bpy` |
| `bmesh` | `bmesh` |
| `mathutils` | `mathutils` |

```python
# what a stage sends
result = bpy.data.objects["Cube"].name
```

Printed output is sent back, an exception comes back as an error of that execution and
Blender keeps working. Executions run one at a time, handed to the main thread by a timer
every 20 ms at most: while a long script runs, Blender's UI is busy as with any script
run in the Text Editor.

## Logging

Connections are logged to `nyx_bridge_blender.client` (and `nyx_bridge.client`) at
`INFO`.
