"""Client connecting a running Blender to Nyx.

`bpy` is imported when it is needed, so the package can be imported (by tools, docs)
outside of Blender.
"""

from __future__ import annotations

import logging
import queue
import threading
import typing

from nyx_bridge.client import NyxClient

LOGGER = logging.getLogger(__name__)


class MainThreadPump:
    """Runs functions on the main thread of Blender for threads that need it.

    Blender's Python API may only be used from the main thread. The pump lets other
    threads hand it a function and wait for the result: a timer of Blender, which runs
    on the main thread, picks the functions up (`run_pending`).
    """

    INTERVAL = 0.02
    """Seconds between looks for work, so a request waits at most this long."""

    def __init__(self) -> None:
        """Initialize MainThreadPump."""
        self._jobs: queue.Queue[_Job] = queue.Queue()
        self._active = False
        # Blender finds a timer by the identity of its function, and a bound method
        # is a new object every time it is asked for.
        self._timer = self._tick

    @property
    def is_active(self) -> bool:
        """bool: the pump takes functions."""
        return self._active

    def start(self) -> None:
        """Start taking functions and ask Blender's timers to run them.

        Call it from the main thread.
        """
        import bpy

        self._active = True
        if not bpy.app.timers.is_registered(self._timer):
            bpy.app.timers.register(self._timer, first_interval=0.0, persistent=True)

    def stop(self) -> None:
        """Stop taking functions. Those waiting fail. Safe to call from any thread."""
        self._active = False

    def submit(self, func: typing.Callable[[], typing.Any]) -> typing.Any:
        """Run a function on the main thread and wait for its result.

        Args:
            func (Callable[[], Any]): function to run.

        Raises:
            RuntimeError: the pump is not running.

        Returns:
            Any: whatever the function returns. What it raises is raised here.
        """
        if not self._active:
            raise RuntimeError("Nothing runs functions on the main thread of Blender")
        job = _Job(func)
        self._jobs.put(job)
        job.done.wait()
        if job.error is not None:
            raise job.error
        return job.result

    def run_pending(self) -> None:
        """Run the functions that are waiting. Call it from the main thread."""
        while True:
            try:
                job = self._jobs.get_nowait()
            except queue.Empty:
                return
            if self._active:
                job.run()
            else:
                job.fail(RuntimeError("The client was stopped"))

    def _tick(self) -> float | None:
        """Timer of Blender: run what is waiting.

        Returns:
            float | None: seconds until the next call, None to remove the timer.
        """
        self.run_pending()
        return self.INTERVAL if self._active else None


class _Job:
    """A function waiting for the main thread, and its outcome."""

    def __init__(self, func: typing.Callable[[], typing.Any]) -> None:
        self.func = func
        self.result: typing.Any = None
        self.error: BaseException | None = None
        self.done = threading.Event()

    def run(self) -> None:
        """Run the function and wake the thread waiting for it."""
        try:
            self.result = self.func()
        except BaseException as err:  # handed to the waiting thread
            self.error = err
        finally:
            self.done.set()

    def fail(self, error: BaseException) -> None:
        """Wake the thread waiting for the job with an error."""
        self.error = error
        self.done.set()


class BlenderClient(NyxClient):
    """Nyx client living in Blender.

    What Nyx sends is run on Blender's main thread, so it can use `bpy` safely.
    Scripts find `bpy`, `bmesh` and `mathutils` in their namespace.

    Serve from a background thread (`start_in_thread`, what `start` does) in a Blender
    with a window. In `blender --background` serve from the main thread with
    `serve_forever`: there is no event loop to hand work over to.
    """

    CLIENT_KIND = "blender"

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        """Initialize BlenderClient, see `NyxClient`."""
        super().__init__(*args, **kwargs)
        self._pump = MainThreadPump()

    def client_version(self) -> str:
        """str: version of Blender."""
        import bpy

        return str(bpy.app.version_string)

    def default_namespace(self) -> dict[str, typing.Any]:
        """Names available to every script run by Nyx.

        Returns:
            dict[str, Any]: `bpy`, `bmesh` and `mathutils`.
        """
        import bmesh
        import bpy
        import mathutils

        return {"bpy": bpy, "bmesh": bmesh, "mathutils": mathutils}

    def start_in_thread(self, connect_timeout: float | None = None) -> threading.Thread:
        """Serve from a background thread, handing requests to the main thread.

        Call it from the main thread: the timer that runs the requests is set up here.

        Args:
            connect_timeout (float | None): see `NyxClient.serve_forever`.

        Returns:
            threading.Thread: running thread.
        """
        self._pump.start()
        return super().start_in_thread(connect_timeout)

    def stop(self) -> None:
        """Stop serving and drop the connection. Safe to call from any thread."""
        self._pump.stop()
        super().stop()

    def run_on_main_thread(self, func: typing.Callable[[], typing.Any]) -> typing.Any:
        """Run a function on Blender's main thread and wait for its result.

        Args:
            func (Callable[[], Any]): function to run.

        Returns:
            Any: whatever the function returns.
        """
        if threading.current_thread() is threading.main_thread():
            return func()
        return self._pump.submit(func)

    def on_connected(self) -> None:
        """Log that Nyx is connected."""
        LOGGER.info("Connected to Nyx (%s) as %s", self.server_name, self.name)

    def on_disconnected(self) -> None:
        """Log that the connection to Nyx ended."""
        LOGGER.info("Disconnected from Nyx")


_client: BlenderClient | None = None
_thread: threading.Thread | None = None


def get_client() -> BlenderClient | None:
    """BlenderClient | None: the client started by `start`, None if there is none."""
    return _client


def is_running() -> bool:
    """bool: the client started by `start` is serving, connected or not."""
    return _thread is not None and _thread.is_alive()


def is_connected() -> bool:
    """bool: the client started by `start` has a connection to Nyx."""
    return is_running() and _client is not None and _client.is_connected


def start(
    address: str | tuple[str, int] | None = None,
    token: str | None = None,
    name: str | None = None,
) -> BlenderClient:
    """Connect Blender to Nyx from a background thread, and keep trying until it works.

    Where Nyx is comes from the arguments, then the environment, then the address file
    Nyx writes, see `nyx_bridge.protocol.find_server_address`. It does not matter
    whether Nyx is already running: the client connects once it is, and again if
    the connection drops. Call it from the main thread.

    Args:
        address (str | tuple[str, int] | None): `host:port` of Nyx.
        token (str | None): token of the Nyx server.
        name (str | None): name Nyx shows for this Blender. Derived from the process id
            if omitted.

    Returns:
        BlenderClient: the running client. An already running one is returned as it
            is, the arguments are ignored.
    """
    global _client, _thread
    if is_running():
        return _client
    _client = BlenderClient(name=name, address=address, token=token)
    _thread = _client.start_in_thread()
    return _client


def stop() -> None:
    """Disconnect from Nyx and stop the client started by `start`."""
    global _client, _thread
    client, thread = _client, _thread
    _client = _thread = None
    if client is not None:
        client.stop()
    if thread is not None and thread is not threading.current_thread():
        thread.join(timeout=5)
