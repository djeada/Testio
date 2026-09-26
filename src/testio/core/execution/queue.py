"""
Execution queue for managing test execution with resource limits.
Provides queuing, prioritization, and resource management.

``max_workers`` worker threads pull tasks from a bounded priority queue, so at
most ``max_workers`` tasks run at the same time and a full queue is reported
immediately (:class:`QueueFullError`) instead of piling up requests.

Callers on an event loop use :meth:`ExecutionQueue.submit_async`, which awaits
the task's future without tying up a thread per waiting request.
"""

import asyncio
import itertools
import logging
import os
import threading
import time
from concurrent.futures import Future, ProcessPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from enum import Enum
from queue import Empty, Full, PriorityQueue
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)

# How long a result fetched through the task-id API is kept if nobody asks
# for it; results are otherwise removed as soon as they are retrieved.
RESULT_TTL_SECONDS = 300.0


class QueueFullError(RuntimeError):
    """Raised by ``submit`` when the pending queue is at capacity."""

    def __init__(self, message: str = "Queue is full", retry_after: int = 5):
        super().__init__(message)
        self.retry_after = retry_after


class ExecutionPriority(Enum):
    """Priority levels for execution tasks."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


_sequence = itertools.count()


@dataclass(order=True)
class ExecutionTask:
    """A task to be executed in the queue."""

    priority: int
    # Tie-breaker so tasks of equal priority run in submission order.
    sequence: int = field(default_factory=lambda: next(_sequence))
    task_id: str = field(compare=False, default="")
    func: Optional[Callable] = field(compare=False, default=None)
    args: Tuple = field(compare=False, default_factory=tuple)
    kwargs: Dict[str, Any] = field(compare=False, default_factory=dict)
    created_at: float = field(compare=False, default_factory=time.time)
    timeout: Optional[float] = field(compare=False, default=None)
    # Resolved when a worker starts the task / when the task finishes.
    started: Future = field(compare=False, default_factory=Future)
    future: Future = field(compare=False, default_factory=Future)
    # Only tasks submitted through the task-id API keep an ExecutionResult.
    retain_result: bool = field(compare=False, default=True)


@dataclass
class ExecutionResult:
    """Result of a task execution."""

    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    queued_time: float = 0.0
    completed_at: float = field(default_factory=time.time)


class ResourceLimiter:
    """
    Manages resource limits for execution.
    Tracks CPU, memory, and concurrent execution limits.
    """

    def __init__(
        self,
        max_concurrent: int = 4,
        max_memory_mb: int = 512,
        max_cpu_time: float = 60.0,
    ):
        """
        Initialize the resource limiter.

        :param max_concurrent: Maximum concurrent executions
        :param max_memory_mb: Maximum memory per execution in MB
        :param max_cpu_time: Maximum CPU time per execution in seconds
        """
        self.max_concurrent = max_concurrent
        self.max_memory_mb = max_memory_mb
        self.max_cpu_time = max_cpu_time
        self._active_count = 0
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        """
        Try to acquire an execution slot.

        :return: True if slot acquired, False otherwise
        """
        with self._lock:
            if self._active_count < self.max_concurrent:
                self._active_count += 1
                return True
            return False

    def release(self) -> None:
        """Release an execution slot."""
        with self._lock:
            self._active_count = max(0, self._active_count - 1)

    @property
    def available_slots(self) -> int:
        """Get number of available execution slots."""
        with self._lock:
            return self.max_concurrent - self._active_count

    @property
    def active_count(self) -> int:
        """Get number of active executions."""
        with self._lock:
            return self._active_count

    def get_stats(self) -> Dict[str, Any]:
        """Get resource limiter statistics."""
        with self._lock:
            return {
                "max_concurrent": self.max_concurrent,
                "active_count": self._active_count,
                "available_slots": self.max_concurrent - self._active_count,
                "max_memory_mb": self.max_memory_mb,
                "max_cpu_time": self.max_cpu_time,
            }


class ExecutionQueue:
    """
    Manages a queue of execution tasks with priority and resource limits.

    ``max_workers`` worker threads each run one task at a time, so tasks are
    executed concurrently up to that bound.
    """

    def __init__(
        self,
        max_workers: int = 4,
        max_queue_size: int = 100,
        default_timeout: float = 30.0,
        use_threads: bool = True,
        max_queue_wait: float = 600.0,
    ):
        """
        Initialize the execution queue.

        :param max_workers: Maximum number of concurrently executing tasks
        :param max_queue_size: Maximum number of tasks waiting to start
        :param default_timeout: Default execution timeout for tasks in seconds
            (time spent waiting in the queue does not count)
        :param use_threads: Run tasks directly on the worker threads (True,
            default) instead of in a ProcessPoolExecutor. Prefer threads when
            tasks already launch subprocesses internally (e.g.
            ExecutionManager.run), to avoid fork-in-multithreaded-process issues.
        :param max_queue_wait: Upper bound on how long a waiter waits for its
            task to *start* before giving up.
        """
        self._max_workers = max(1, int(max_workers))
        self._max_queue_size = max_queue_size
        self._default_timeout = default_timeout
        self._max_queue_wait = max_queue_wait

        self._queue: PriorityQueue = PriorityQueue(maxsize=max_queue_size)
        self._process_pool: Optional[ProcessPoolExecutor] = (
            None if use_threads else ProcessPoolExecutor(max_workers=self._max_workers)
        )
        self._resource_limiter = ResourceLimiter(max_concurrent=self._max_workers)

        self._results: Dict[str, ExecutionResult] = {}
        self._pending: Dict[str, ExecutionTask] = {}
        self._lock = threading.RLock()

        self._running = False
        self._workers: List[threading.Thread] = []

        # Statistics
        self._total_submitted = 0
        self._total_completed = 0
        self._total_failed = 0
        self._total_timeouts = 0
        self._total_rejected = 0

    @property
    def max_workers(self) -> int:
        """Number of tasks that can execute at the same time."""
        return self._max_workers

    def start(self) -> None:
        """Start the worker threads."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._workers = [
                threading.Thread(
                    target=self._worker_loop,
                    name=f"testio-exec-{index}",
                    daemon=True,
                )
                for index in range(self._max_workers)
            ]
            for worker in self._workers:
                worker.start()
            logger.info("Execution queue started with %d workers", self._max_workers)

    def stop(self) -> None:
        """Stop the workers; tasks still waiting in the queue are failed."""
        with self._lock:
            self._running = False
            workers = list(self._workers)
            self._workers = []

        for worker in workers:
            worker.join(timeout=5.0)

        while True:
            try:
                task = self._queue.get_nowait()
            except Empty:
                break
            self._fail_unstarted(task, RuntimeError("Execution queue stopped"))

        if self._process_pool is not None:
            self._process_pool.shutdown(wait=False)
        logger.info("Execution queue stopped")

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def _enqueue(
        self,
        func: Callable,
        args: Tuple,
        kwargs: Dict[str, Any],
        priority: ExecutionPriority,
        timeout: Optional[float],
        retain_result: bool,
    ) -> ExecutionTask:
        task = ExecutionTask(
            priority=priority.value,
            task_id=str(uuid4()),
            func=func,
            args=args,
            kwargs=kwargs,
            timeout=timeout or self._default_timeout,
            retain_result=retain_result,
        )
        with self._lock:
            # Register first so a worker that picks the task up immediately
            # does not mistake it for a cancelled one.
            self._pending[task.task_id] = task
            try:
                self._queue.put_nowait(task)
            except Full:
                del self._pending[task.task_id]
                self._total_rejected += 1
                logger.warning("Execution queue full; rejecting task")
                raise QueueFullError() from None
            self._total_submitted += 1
        logger.debug(f"Task {task.task_id} submitted with priority {priority.name}")
        return task

    def submit(
        self,
        func: Callable,
        *args,
        priority: ExecutionPriority = ExecutionPriority.NORMAL,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> str:
        """
        Submit a task for execution.

        :param func: Function to execute
        :param args: Positional arguments
        :param priority: Task priority
        :param timeout: Optional execution-timeout override
        :param kwargs: Keyword arguments
        :return: Task ID (use ``wait_for_result`` / ``get_result``)
        :raises QueueFullError: If the queue is at capacity
        """
        return self._enqueue(func, args, kwargs, priority, timeout, True).task_id

    def submit_sync(
        self,
        func: Callable,
        *args,
        priority: "ExecutionPriority" = ExecutionPriority.HIGH,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Any:
        """
        Submit and wait for task completion synchronously.

        :param func: Function to execute
        :param args: Positional arguments
        :param priority: Task priority (default HIGH for synchronous callers)
        :param timeout: Optional execution timeout (queue time excluded)
        :param kwargs: Keyword arguments
        :return: Task result
        :raises QueueFullError: If the queue is at capacity
        :raises TimeoutError: If the task does not finish in time
        """
        task = self._enqueue(func, args, kwargs, priority, timeout, False)
        try:
            task.started.result(timeout=self._max_queue_wait)
            return task.future.result(timeout=task.timeout)
        except FutureTimeoutError:
            self._on_wait_timeout(task)
            raise TimeoutError(
                f"Task {task.task_id} did not complete within {task.timeout}s"
            ) from None

    async def submit_async(
        self,
        func: Callable,
        *args,
        priority: "ExecutionPriority" = ExecutionPriority.NORMAL,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Any:
        """
        Submit a task and await its result without blocking the event loop.

        The execution timeout starts when a worker picks the task up, so time
        spent waiting behind other tasks is not counted against it.

        :param func: Function to execute
        :param args: Positional arguments
        :param priority: Task priority (default NORMAL for async callers)
        :param timeout: Optional execution timeout
        :param kwargs: Keyword arguments
        :return: Task result
        :raises QueueFullError: If the queue is at capacity
        :raises TimeoutError: If the task does not finish in time
        """
        task = self._enqueue(func, args, kwargs, priority, timeout, False)
        try:
            await asyncio.wait_for(
                asyncio.shield(asyncio.wrap_future(task.started)),
                timeout=self._max_queue_wait,
            )
            return await asyncio.wait_for(
                asyncio.shield(asyncio.wrap_future(task.future)),
                timeout=task.timeout,
            )
        except asyncio.TimeoutError:
            self._on_wait_timeout(task)
            raise TimeoutError(
                f"Task {task.task_id} did not complete within {task.timeout}s"
            ) from None
        except asyncio.CancelledError:
            # The client went away: don't start the task if it is still queued.
            self.cancel(task.task_id)
            raise

    def get_result(self, task_id: str) -> Optional[ExecutionResult]:
        """
        Get the result of a completed task (without removing it).

        :param task_id: The task ID
        :return: ExecutionResult or None if not complete
        """
        with self._lock:
            return self._results.get(task_id)

    def wait_for_result(
        self, task_id: str, timeout: float = 60.0, poll_interval: float = 0.1
    ) -> Any:
        """
        Wait for a task to complete and return its result.

        The stored result is removed once it has been returned.

        :param task_id: The task ID
        :param timeout: Maximum time to wait for the execution itself
        :param poll_interval: Unused; kept for backward compatibility
        :return: Task result
        :raises TimeoutError: If task doesn't complete in time
        :raises RuntimeError: If task failed
        """
        with self._lock:
            task = self._pending.get(task_id)
            result = self._results.pop(task_id, None)

        if result is None and task is not None:
            try:
                task.started.result(timeout=self._max_queue_wait)
                task.future.result(timeout=timeout)
            except FutureTimeoutError:
                self._on_wait_timeout(task)
                raise TimeoutError(
                    f"Task {task_id} did not complete within {timeout}s"
                ) from None
            except Exception:  # noqa: BLE001 - the stored result carries it
                pass
            with self._lock:
                result = self._results.pop(task_id, None)

        if result is None:
            raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")
        if result.success:
            return result.result
        raise RuntimeError(result.error or "Task execution failed")

    def cancel(self, task_id: str) -> bool:
        """
        Cancel a pending task.

        :param task_id: The task ID
        :return: True if cancelled, False if already executing/completed
        """
        with self._lock:
            task = self._pending.get(task_id)
            # Future.cancel() fails once a worker has marked the task running.
            if task is None or not task.started.cancel():
                return False
            del self._pending[task_id]
        task.future.cancel()
        logger.info(f"Task {task_id} cancelled")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self._lock:
            return {
                "running": self._running,
                "workers": self._max_workers,
                "queue_size": self._queue.qsize(),
                "max_queue_size": self._max_queue_size,
                "pending_count": len(self._pending),
                "completed_count": len(self._results),
                "total_submitted": self._total_submitted,
                "total_completed": self._total_completed,
                "total_failed": self._total_failed,
                "total_timeouts": self._total_timeouts,
                "total_rejected": self._total_rejected,
                "resources": self._resource_limiter.get_stats(),
            }

    # ------------------------------------------------------------------
    # Worker side
    # ------------------------------------------------------------------

    def _on_wait_timeout(self, task: ExecutionTask) -> None:
        """A waiter gave up: drop the task if it has not started yet."""
        with self._lock:
            self._total_timeouts += 1
        self.cancel(task.task_id)

    def _fail_unstarted(self, task: ExecutionTask, error: Exception) -> None:
        with self._lock:
            self._pending.pop(task.task_id, None)
        if task.started.set_running_or_notify_cancel():
            task.started.set_result(None)
        if not task.future.done():
            task.future.set_exception(error)

    def _worker_loop(self) -> None:
        """Worker loop: take the next task and run it to completion."""
        while self.is_running:
            try:
                task = self._queue.get(timeout=0.5)
            except Empty:
                continue

            try:
                with self._lock:
                    cancelled = task.task_id not in self._pending
                if cancelled or not task.started.set_running_or_notify_cancel():
                    continue
                task.future.set_running_or_notify_cancel()
                self._resource_limiter.acquire()
                try:
                    self._execute_task(task)
                finally:
                    self._resource_limiter.release()
            except Exception as e:  # pragma: no cover - defensive
                logger.error(f"Worker loop error: {e}")
            finally:
                self._queue.task_done()

    def _execute_task(self, task: ExecutionTask) -> None:
        """
        Execute a single task on the current worker thread.

        :param task: The task to execute
        """
        start_time = time.time()
        queued_time = start_time - task.created_at
        task.started.set_result(start_time)

        try:
            if self._process_pool is not None:
                result = self._process_pool.submit(
                    task.func, *task.args, **task.kwargs
                ).result()
            else:
                result = task.func(*task.args, **task.kwargs)
        except Exception as e:  # noqa: BLE001 - reported to the waiter
            execution_time = time.time() - start_time
            self._finish(
                task,
                ExecutionResult(
                    task_id=task.task_id,
                    success=False,
                    error=str(e),
                    execution_time=execution_time,
                    queued_time=queued_time,
                ),
            )
            task.future.set_exception(e)
            logger.error(f"Task {task.task_id} failed: {e}")
            return

        execution_time = time.time() - start_time
        self._finish(
            task,
            ExecutionResult(
                task_id=task.task_id,
                success=True,
                result=result,
                execution_time=execution_time,
                queued_time=queued_time,
            ),
        )
        task.future.set_result(result)
        logger.debug(f"Task {task.task_id} completed in {execution_time:.2f}s")

    def _finish(self, task: ExecutionTask, result: ExecutionResult) -> None:
        with self._lock:
            self._pending.pop(task.task_id, None)
            if result.success:
                self._total_completed += 1
            else:
                self._total_failed += 1
            if task.retain_result:
                self._results[task.task_id] = result
            self._prune_results()

    def _prune_results(self) -> None:
        """Drop results nobody collected within RESULT_TTL_SECONDS."""
        cutoff = time.time() - RESULT_TTL_SECONDS
        stale = [
            key for key, value in self._results.items() if value.completed_at < cutoff
        ]
        for key in stale:
            del self._results[key]


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, default)))
    except ValueError:
        logger.warning("Ignoring invalid %s=%r", name, os.environ.get(name))
        return default


def get_max_concurrent_executions() -> int:
    """Concurrent test executions (TESTIO_MAX_CONCURRENT_EXECUTIONS, default 4)."""
    return _env_int("TESTIO_MAX_CONCURRENT_EXECUTIONS", 4)


def get_max_queue_size() -> int:
    """Tasks allowed to wait for a worker (TESTIO_EXECUTION_QUEUE_SIZE, default 100)."""
    return _env_int("TESTIO_EXECUTION_QUEUE_SIZE", 100)


# Global execution queue
_global_queue: Optional[ExecutionQueue] = None
_queue_lock = threading.Lock()


def get_execution_queue() -> ExecutionQueue:
    """
    Get or create the global execution queue.

    :return: The global ExecutionQueue instance
    """
    global _global_queue
    if _global_queue is None or not _global_queue.is_running:
        with _queue_lock:
            if _global_queue is None or not _global_queue.is_running:
                _global_queue = ExecutionQueue(
                    max_workers=get_max_concurrent_executions(),
                    max_queue_size=get_max_queue_size(),
                )
                _global_queue.start()
    return _global_queue
