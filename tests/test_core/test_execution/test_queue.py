"""Tests for the execution queue."""

import asyncio
import threading
import time

import pytest

from testio.core.execution.queue import ExecutionQueue, QueueFullError


@pytest.fixture
def queue():
    q = ExecutionQueue(max_workers=4, max_queue_size=10)
    q.start()
    yield q
    q.stop()


def test_tasks_run_concurrently_up_to_max_workers(queue):
    async def main():
        start = time.monotonic()
        results = await asyncio.gather(
            *(queue.submit_async(time.sleep, 0.3) for _ in range(4))
        )
        return results, time.monotonic() - start

    results, elapsed = asyncio.run(main())
    assert results == [None] * 4
    # Serial execution would take >= 1.2s.
    assert elapsed < 0.9


def test_concurrency_is_bounded():
    q = ExecutionQueue(max_workers=2, max_queue_size=10)
    q.start()
    active = 0
    peak = 0
    lock = threading.Lock()

    def work():
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.1)
        with lock:
            active -= 1

    async def main():
        await asyncio.gather(*(q.submit_async(work) for _ in range(6)))

    try:
        asyncio.run(main())
    finally:
        q.stop()
    assert peak == 2


def test_submit_async_does_not_block_event_loop(queue):
    async def main():
        ticks = 0

        async def ticker():
            nonlocal ticks
            for _ in range(5):
                await asyncio.sleep(0.02)
                ticks += 1

        await asyncio.gather(queue.submit_async(time.sleep, 0.3), ticker())
        return ticks

    assert asyncio.run(main()) == 5


def test_full_queue_raises_queue_full_error():
    q = ExecutionQueue(max_workers=1, max_queue_size=1)  # workers not started
    q.submit(time.sleep, 0)
    with pytest.raises(QueueFullError):
        q.submit(time.sleep, 0)
    assert q.get_stats()["total_rejected"] == 1
    q.stop()


def test_timeout_excludes_queue_time():
    q = ExecutionQueue(max_workers=1, max_queue_size=10)
    q.start()

    async def main():
        # Second task waits ~0.4s in the queue but runs for only ~0.1s, so a
        # 0.3s execution timeout must not trip.
        return await asyncio.gather(
            q.submit_async(time.sleep, 0.4, timeout=5),
            q.submit_async(lambda: time.sleep(0.1) or "done", timeout=0.3),
        )

    try:
        assert asyncio.run(main())[1] == "done"
    finally:
        q.stop()


def test_execution_timeout_raises(queue):
    async def main():
        await queue.submit_async(time.sleep, 0.5, timeout=0.1)

    with pytest.raises(TimeoutError):
        asyncio.run(main())


def test_errors_propagate(queue):
    def fail():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        queue.submit_sync(fail)
    with pytest.raises(RuntimeError, match="boom"):
        queue.wait_for_result(queue.submit(fail), timeout=5)


def test_results_are_pruned_after_retrieval(queue):
    task_id = queue.submit(lambda: 42)
    assert queue.wait_for_result(task_id, timeout=5) == 42
    assert queue.get_result(task_id) is None
    # Async/sync submissions never accumulate results.
    queue.submit_sync(lambda: 1)
    asyncio.run(queue.submit_async(lambda: 2))
    assert queue.get_stats()["completed_count"] == 0


def test_cancel_pending_task():
    q = ExecutionQueue(max_workers=1, max_queue_size=10)  # not started
    task_id = q.submit(time.sleep, 0)
    assert q.cancel(task_id) is True
    assert q.cancel(task_id) is False
    q.stop()
