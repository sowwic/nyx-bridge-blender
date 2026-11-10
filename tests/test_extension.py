import importlib.util
import pathlib
import sys
import time
import types

import pytest
from nyx_bridge.server import BridgeServer

import nyx_bridge_blender

EXTENSION_DIR = pathlib.Path(__file__).resolve().parent.parent / "extension"
PACKAGE = "nyx_extension_under_test"


@pytest.fixture
def extension():
    """The extension loaded from its source folder and registered."""
    spec = importlib.util.spec_from_file_location(
        PACKAGE,
        EXTENSION_DIR / "__init__.py",
        submodule_search_locations=[str(EXTENSION_DIR)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE] = module
    spec.loader.exec_module(module)
    module.register()
    yield module
    module.unregister()
    for name in [name for name in sys.modules if name.startswith(PACKAGE)]:
        del sys.modules[name]


@pytest.fixture
def server():
    with BridgeServer(name="test", port=0) as running:
        yield running


def wait_until(predicate, timeout=15):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        time.sleep(0.05)
    return predicate()


def test_register_adds_the_operators_the_panel_and_the_preferences(extension):
    import bpy

    assert hasattr(bpy.ops.nyx, "connect")
    assert hasattr(bpy.ops.nyx, "disconnect")
    assert hasattr(bpy.types, "NYX_PT_bridge")
    assert bpy.types.AddonPreferences.bl_rna_get_subclass_py("NYX_AP_preferences")


def test_unregister_removes_them_and_disconnects(server):
    import bpy

    spec = importlib.util.spec_from_file_location(
        PACKAGE,
        EXTENSION_DIR / "__init__.py",
        submodule_search_locations=[str(EXTENSION_DIR)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE] = module
    spec.loader.exec_module(module)
    module.register()
    nyx_bridge_blender.start(
        address=(server.host, server.port), token=server.token, name="unload"
    )
    server.wait_for_client(name="unload", timeout=15)

    module.unregister()

    assert not nyx_bridge_blender.is_running()
    assert wait_until(lambda: not server.clients)
    assert not hasattr(bpy.types, "NYX_PT_bridge")
    assert not hasattr(bpy.types, "NYX_OT_connect")
    assert (
        bpy.types.AddonPreferences.bl_rna_get_subclass_py("NYX_AP_preferences") is None
    )
    del sys.modules[PACKAGE]


def test_connect_and_disconnect_operators_drive_the_client(
    extension, server, monkeypatch
):
    import bpy

    monkeypatch.setenv("NYX_BRIDGE_ADDRESS", f"{server.host}:{server.port}")
    monkeypatch.setenv("NYX_BRIDGE_TOKEN", server.token)

    assert bpy.ops.nyx.connect() == {"FINISHED"}
    try:
        assert nyx_bridge_blender.is_running()
        assert server.wait_for_client(kind="blender", timeout=15)
    finally:
        assert bpy.ops.nyx.disconnect() == {"FINISHED"}

    assert not nyx_bridge_blender.is_running()


def test_connection_arguments_come_from_the_preferences(extension):
    preferences = importlib.import_module(f"{PACKAGE}.preferences")
    settings = types.SimpleNamespace(
        address=" 10.0.0.2:5000 ", token="s3", client_name=""
    )

    assert preferences.connection_arguments(settings) == {
        "address": "10.0.0.2:5000",
        "token": "s3",
        "name": None,
    }
    assert preferences.connection_arguments(None) == {
        "address": None,
        "token": None,
        "name": None,
    }


def test_preferences_are_none_while_the_extension_is_not_an_enabled_add_on(extension):
    preferences = importlib.import_module(f"{PACKAGE}.preferences")

    assert preferences.get_preferences() is None


def test_auto_connect_starts_the_client_when_the_preferences_ask(
    extension, server, monkeypatch
):
    settings = types.SimpleNamespace(
        address=f"{server.host}:{server.port}",
        token=server.token,
        client_name="auto",
        auto_connect=True,
    )
    monkeypatch.setattr(extension.preferences, "get_preferences", lambda *a: settings)

    extension._auto_connect()
    try:
        assert server.wait_for_client(name="auto", timeout=15)
    finally:
        nyx_bridge_blender.stop()


def test_auto_connect_does_nothing_when_it_is_off(extension, monkeypatch):
    settings = types.SimpleNamespace(
        address="", token="", client_name="", auto_connect=False
    )
    monkeypatch.setattr(extension.preferences, "get_preferences", lambda *a: settings)

    extension._auto_connect()

    assert not nyx_bridge_blender.is_running()
