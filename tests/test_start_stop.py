import time

import pytest
from nyx_bridge.server import BridgeServer

import nyx_bridge_blender


@pytest.fixture
def server():
    with BridgeServer(name="test", port=0) as running:
        yield running


def wait_until(predicate, timeout=15):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        time.sleep(0.05)
    return predicate()


def test_start_connects_one_client_and_stop_ends_it(server):
    client = nyx_bridge_blender.start(
        address=(server.host, server.port), token=server.token, name="api"
    )
    try:
        assert nyx_bridge_blender.is_running()
        assert nyx_bridge_blender.get_client() is client
        assert nyx_bridge_blender.start() is client
        session = server.wait_for_client(name="api", kind="blender", timeout=15)
        assert session.kind == "blender"
        assert wait_until(nyx_bridge_blender.is_connected)
    finally:
        nyx_bridge_blender.stop()

    assert not nyx_bridge_blender.is_running()
    assert nyx_bridge_blender.get_client() is None
    assert wait_until(lambda: not server.clients)


def test_start_waits_for_nyx_to_appear():
    client = nyx_bridge_blender.start(address=("127.0.0.1", 9), name="waiting")
    try:
        time.sleep(0.3)
        assert nyx_bridge_blender.is_running()
        assert not nyx_bridge_blender.is_connected()
    finally:
        nyx_bridge_blender.stop()
    assert client is not None


def test_serve_background_takes_its_name_from_the_environment_and_ends_on_shutdown(
    server, monkeypatch
):
    import threading

    monkeypatch.setenv(
        nyx_bridge_blender.client.CLIENT_NAME_VARIABLE, "from-environment"
    )
    outcome = {}

    def drive():
        try:
            session = server.wait_for_client(name="from-environment", timeout=15)
            outcome["kind"] = session.kind
            outcome["version"] = session.execute(
                "bpy.app.version_string", mode="eval", timeout=15
            ).value
            session.request_shutdown()
        except Exception as err:  # raised on the main thread below
            outcome["error"] = err

    driver = threading.Thread(target=drive)
    driver.start()
    nyx_bridge_blender.serve_background(
        address=(server.host, server.port), token=server.token, connect_timeout=15
    )
    driver.join(timeout=15)

    assert "error" not in outcome, outcome.get("error")
    assert outcome["kind"] == "blender"
    assert outcome["version"]
    assert wait_until(lambda: not server.clients)


def test_serve_background_does_not_reconnect_when_nyx_goes_away(server):
    import threading

    def drop():
        server.wait_for_client(kind="blender", timeout=15).close()

    dropper = threading.Thread(target=drop)
    dropper.start()
    nyx_bridge_blender.serve_background(
        name="dropped", address=(server.host, server.port), token=server.token
    )
    dropper.join(timeout=15)
