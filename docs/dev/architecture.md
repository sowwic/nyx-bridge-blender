# Architecture

```text
src
└── nyx_bridge_blender
    ├── client.py    BlenderClient, MainThreadPump, start/stop/is_*, serve_background
    └── version.py   __version__
extension
├── __init__.py             register / unregister, connect on start
├── blender_manifest.toml   the extension manifest
├── operators.py            nyx.connect, nyx.disconnect
├── panel.py                sidebar panel and its redraw timer
└── preferences.py          address, token, name, connect on start
scripts/build_extension.py  assembles and builds the zip
```

`BlenderClient` is a subclass of `nyx_bridge.client.NyxClient`; see
[Writing a client](https://sowwic.github.io/nyx-bridge/dev/clients/) for what each hook is.

| Member | Blender specific |
| --- | --- |
| `CLIENT_KIND` | `"blender"` |
| `client_version()` | `bpy.app.version_string` |
| `default_namespace()` | `bpy`, `bmesh`, `mathutils` |
| `run_on_main_thread(func)` | Runs `func` directly on the main thread, else hands it to the `MainThreadPump`. |
| `start_in_thread()` / `stop()` | Also start and stop the pump. |

## Two ways to serve

- **Blender with a window**: `start()` uses `start_in_thread()`. The reading loop lives on
  a daemon thread, and every execution is handed to the main thread through the pump.
- **`blender --background`**: there is no event loop to run timers, so handing work over
  would wait forever. `serve_background()` serves from the main thread with
  `serve_forever()`, where `run_on_main_thread` calls `func` straight away.
  `reconnect=False`, since the process is started for one stage.

## The main-thread pump

Blender's API may only be used from the main thread, and has no `executeInMainThread`.
`MainThreadPump` fills that gap:

1. A worker thread calls `submit(func)`, which queues a job and waits on its event.
2. A timer registered with `bpy.app.timers` (every `INTERVAL`, 20 ms) calls
   `run_pending()` on the main thread, which runs the jobs and wakes the waiters with
   the result or the exception.
3. `stop()` makes the timer return `None` (removing it) and fails the jobs still waiting,
   so no thread hangs on a stopped client.

The timer function is stored once (`self._timer`): Blender finds a timer by the identity
of its function, and a bound method is a new object every time it is asked for. The
timer is `persistent`, so it survives loading another file.

`start_in_thread()` must be called from the main thread, since that is where the timer is
registered.

## Module state

`client.py` keeps one client and its thread in module globals. `start()` returns the
running one, `stop()` clears them and joins the thread (5 s). The extension's
`unregister` calls `stop()`, so disabling it never leaves a connection behind.

## The extension

`register()` adds the preferences, the two operators and the panel, starts the redraw
timer (1 s, so the panel follows the connection) and, after `AUTO_CONNECT_DELAY`, a timer
that connects when **Connect on start** is on. `connection_arguments()` turns the
preferences into the arguments of `start()`, `None` for empty fields.
`get_preferences()` returns `None` while the extension is not enabled as an add-on, as in
tests.

## The zip

`scripts/build_extension.py` copies `extension/` into `build/extension/`, builds a wheel
of the package and of every dependency into its `wheels/` folder, writes the list into
`blender_manifest.toml` (at the line `# The wheels are added by ...`), and has Blender
pack it (`blender --command extension build`). Dependencies are built from the git
revision pinned in `[tool.uv.sources]` if it has one, otherwise downloaded from the package
index. The set of dependencies and their versions come from `uv export`, so they match
`uv.lock`, and they must be pure Python wheels. The manifest version
must equal `VERSION`, or the build stops.

The targets come from [sowwic/makefiles](https://github.com/sowwic/makefiles)
(`dcc/blender`), fetched into `.make/` and committed; `make update-make` fetches them
again.
