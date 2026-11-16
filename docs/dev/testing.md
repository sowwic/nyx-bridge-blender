# Testing

The tests run with the [`bpy`](https://pypi.org/project/bpy/) package, Blender as a
Python module, so no Blender install is needed.

```bash
make pytest                                  # everything, with coverage
uv run --group bpy pytest tests -k pump      # a selection
make pytest-pdb                              # verbose, pdb on failure
```

## Setting up

`bpy` is a 250 MB download the first time. Each `bpy` release needs exactly one Python
version: 5.2 needs **3.13** (see `.python-version`), and has no wheel for Intel Macs or
Linux on ARM. It is in its own dependency group, `bpy`, which the make targets add:
`uv sync` alone leaves it out, and does not stop the rest of the project from working.

A plain `pytest` without `bpy` skips everything but `test_package.py` (see
`pytest_collection_modifyitems` in `tests/conftest.py`), so lint and docs jobs need no
Blender. `make validate` checks the extension manifest, which does need a Blender
(`BLENDER` in `.env`, see [Installation](../user/installation.md)).

## Layout

| File | Covers |
| --- | --- |
| `tests/test_package.py` | The package imports (runs without `bpy`). |
| `tests/test_pump.py` | `MainThreadPump`: results, errors, order, stopping, the timer; the client's choice between direct call and pump. |
| `tests/test_client.py` | `BlenderClient` against a real `BridgeServer` over loopback: description, namespace, errors. |
| `tests/test_start_stop.py` | `start`/`stop`, waiting for Nyx to appear, `serve_background`. |
| `tests/test_extension.py` | The extension loaded from `extension/`: registering, operators, preferences, connect on start. |

`tests/conftest.py` provides `output_dir`.

## Fixtures and helpers

- `server` (`BridgeServer(port=0)`): the system picks a free port, so tests can run while
  Nyx is open.
- `make_client(server, **kwargs)` (`test_client.py`): a `BlenderClient` pointed at that
  server with `reconnect=False`.
- `run_remote(server, client, *requests)` (`test_client.py`): the client serves on the
  main thread, as in `blender --background`, while another thread sends the requests and
  collects results.
- `pump` and `serve_until_done(pump, thread)` (`test_pump.py`): the test acts as Blender's
  timer, calling `run_pending()` on the main thread while a thread waits.
- `extension` (`test_extension.py`): loads `extension/` from its folder under a throwaway
  package name, registers it, and unregisters after.
- `wait_until(predicate, timeout=15)` (`test_extension.py`): poll instead of `sleep`.

## What to cover

- A new preference or operator: a test in `test_extension.py` going through the
  registered classes.
- Anything that depends on threads: keep timeouts generous (10 to 15 s) and wait on
  conditions. A flaky test here is almost always a missing wait.
- Behavior that needs Blender's real event loop (the timer firing in a window) can't run
  with `bpy` as a module; test the pump through `run_pending()` and check an interactive
  Blender when a change touches the main-thread hand-off.

## CI

`.github/workflows/unit_tests.yml` calls the shared `python-tests` workflow on hosted
runners with Python 3.13 and the libraries Blender loads (`libegl1`, `libgl1`, ...). It
runs `uv run --group bpy pytest tests`. Lint (`code_quality.yml`) needs no Blender:
`make lint`.
