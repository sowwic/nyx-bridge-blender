import threading

import pytest
from nyx_bridge.server import BridgeServer, RemoteExecutionError

from nyx_bridge_blender.client import BlenderClient

WAIT = 15


@pytest.fixture
def server():
    with BridgeServer(name="test", port=0) as running:
        yield running


def make_client(server, **kwargs):
    return BlenderClient(
        name="blender-test",
        address=(server.host, server.port),
        token=server.token,
        reconnect=False,
        **kwargs,
    )


def run_remote(server, client, *requests):
    """Serve on this (main) thread while another thread sends the requests.

    A background Blender has no event loop to hand work to, so like a batch script the
    client serves from the main thread.

    Returns:
        tuple: the client's session on the server, and the result of every request.
    """
    results, errors, sessions = [], [], []

    def send():
        try:
            session = server.wait_for_client(name=client.name, timeout=WAIT)
            sessions.append(session)
            for code, mode in requests:
                results.append(session.execute(code, mode=mode, timeout=WAIT))
        except Exception as err:  # raised on the main thread below
            errors.append(err)
        finally:
            client.stop()

    sender = threading.Thread(target=send)
    sender.start()
    client.serve_forever(connect_timeout=WAIT)
    sender.join(timeout=WAIT)
    if errors:
        raise errors[0]
    return sessions[0], results


def test_client_describes_blender(server):
    import bpy

    client = make_client(server)

    assert client.CLIENT_KIND == "blender"
    assert client.client_version() == bpy.app.version_string
    assert {"bpy", "bmesh", "mathutils"} <= set(client.default_namespace())


def test_server_sees_a_blender_client(server):
    client = make_client(server)

    session, _ = run_remote(server, client)

    assert (session.name, session.kind) == ("blender-test", "blender")
    assert session.version == client.client_version()


def test_scripts_run_blender_commands_and_keep_their_namespace(server):
    import bpy

    bpy.ops.wm.read_factory_settings(use_empty=True)
    client = make_client(server)

    _, results = run_remote(
        server,
        client,
        (
            "bpy.ops.mesh.primitive_cube_add()\n"
            "cube = bpy.context.active_object\n"
            "cube.name = 'nyx_cube'\n"
            "result = cube.name",
            "exec",
        ),
        ("cube.name in bpy.data.objects", "eval"),
        ("result = len(mathutils.Vector((1, 2, 2)))", "exec"),
        ("result = bpy.app.version_string", "exec"),
    )

    assert [result.value for result in results] == [
        "nyx_cube",
        True,
        3,
        client.client_version(),
    ]
    assert "nyx_cube" in bpy.data.objects


def test_blender_errors_come_back_as_remote_errors(server):
    client = make_client(server)

    with pytest.raises(RemoteExecutionError, match="no_such_attribute"):
        run_remote(server, client, ("bpy.no_such_attribute", "exec"))
