import threading
import time

import pytest

from nyx_bridge_blender.client import BlenderClient, MainThreadPump

WAIT = 10


@pytest.fixture
def pump():
    running = MainThreadPump()
    running.start()
    yield running
    running.stop()


def in_thread(target):
    """Run a function in another thread, return the thread and a dict of its outcome."""
    outcome = {}

    def work():
        try:
            outcome["result"] = target()
        except BaseException as err:
            outcome["error"] = err

    thread = threading.Thread(target=work)
    thread.start()
    return thread, outcome


def serve_until_done(pump, thread):
    """Act as the timer of Blender, which runs on the main thread."""
    deadline = time.monotonic() + WAIT
    while thread.is_alive() and time.monotonic() < deadline:
        pump.run_pending()
        time.sleep(0.005)
    thread.join(timeout=1)


def test_functions_run_on_the_main_thread_and_the_result_comes_back(pump):
    thread, outcome = in_thread(lambda: pump.submit(threading.current_thread))

    serve_until_done(pump, thread)

    assert outcome["result"] is threading.main_thread()


def test_errors_are_raised_in_the_thread_that_asked(pump):
    def fail():
        raise ValueError("from the main thread")

    thread, outcome = in_thread(lambda: pump.submit(fail))

    serve_until_done(pump, thread)

    assert isinstance(outcome["error"], ValueError)
    assert str(outcome["error"]) == "from the main thread"


def test_functions_run_in_the_order_they_were_submitted(pump):
    order = []
    threads = []
    for index in range(5):
        thread, _ = in_thread(
            lambda index=index: pump.submit(lambda: order.append(index))
        )
        threads.append(thread)
        time.sleep(0.02)

    for thread in threads:
        serve_until_done(pump, thread)

    assert order == [0, 1, 2, 3, 4]


def test_submitting_to_a_stopped_pump_fails():
    with pytest.raises(RuntimeError, match="main thread"):
        MainThreadPump().submit(lambda: None)


def test_functions_waiting_when_the_pump_stops_fail(pump):
    thread, outcome = in_thread(lambda: pump.submit(lambda: "never runs"))
    deadline = time.monotonic() + WAIT
    while pump._jobs.empty() and time.monotonic() < deadline:
        time.sleep(0.005)

    pump.stop()
    pump.run_pending()
    thread.join(timeout=WAIT)

    assert isinstance(outcome["error"], RuntimeError)


def test_the_timer_of_blender_is_registered_while_the_pump_runs():
    import bpy

    pump = MainThreadPump()
    pump.start()
    try:
        assert bpy.app.timers.is_registered(pump._timer)
        pump.start()  # a second start does not add a second timer
    finally:
        pump.stop()
    assert pump._tick() is None


def test_the_client_runs_on_the_main_thread_directly_when_it_is_there():
    client = BlenderClient(name="direct")

    assert client.run_on_main_thread(lambda: "ran") == "ran"


def test_the_client_hands_work_from_other_threads_to_the_pump():
    client = BlenderClient(name="pumped")
    client._pump.start()
    try:
        thread, outcome = in_thread(
            lambda: client.run_on_main_thread(threading.current_thread)
        )
        serve_until_done(client._pump, thread)
    finally:
        client.stop()

    assert outcome["result"] is threading.main_thread()
