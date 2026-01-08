"""
Execution queue for managing test execution with resource limits.
Provides queuing, prioritization, and resource management.
"""

import asyncio
import threading
import time
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from enum import Enum, auto
from queue import PriorityQueue, Empty
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class ExecutionPriority(Enum):
    """Priority levels for execution tasks."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass(order=True)
class ExecutionTask:
    """A task to be executed in the queue."""
    priority: int
    task_id: str = field(compare=False)
    func: Callable = field(compare=False)
    args: Tuple = field(compare=False, default_factory=tuple)
    kwargs: Dict[str, Any] = field(compare=False, default_factory=dict)
    created_at: float = field(compare=False, default_factory=time.time)
    timeout: Optional[float] = field(compare=False, default=None)


@dataclass
class ExecutionResult:
    """Result of a task execution."""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    queued_time: float = 0.0


class ResourceLimiter:
    """
    Manages resource limits for execution.
    Tracks CPU, memory, and concurrent execution limits.
    """

    def __init__(
        self,
        max_concurrent: int = 4,
        max_memory_mb: int = 512,
        max_cpu_time: float = 60.0
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
                "max_cpu_time": self.max_cpu_time
            }


class ExecutionQueue:
    """
    Manages a queue of execution tasks with priority and resource limits.
    Uses a combination of priority queue and process pool for execution.
    """

    def __init__(
        self,
        max_workers: int = 4,
        max_queue_size: int = 100,
        default_timeout: float = 30.0
    ):
        """
        Initialize the execution queue.

        :param max_workers: Maximum number of worker processes
        :param max_queue_size: Maximum size of the pending queue
        :param default_timeout: Default timeout for tasks in seconds
        """
        self._max_workers = max_workers
        self._max_queue_size = max_queue_size
        self._default_timeout = default_timeout

        self._queue: PriorityQueue = PriorityQueue(maxsize=max_queue_size)
        self._executor = ProcessPoolExecutor(max_workers=max_workers)
        self._resource_limiter = ResourceLimiter(max_concurrent=max_workers)
        
        self._results: Dict[str, ExecutionResult] = {}
        self._pending: Dict[str, ExecutionTask] = {}
        self._lock = threading.RLock()
        
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None

        # Statistics
        self._total_submitted = 0
        self._total_completed = 0
        self._total_failed = 0
        self._total_timeouts = 0

    def start(self) -> None:
        """Start the execution queue worker."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                daemon=True
            )
            self._worker_thread.start()
            logger.info("Execution queue started")

    def stop(self) -> None:
        """Stop the execution queue worker."""
        with self._lock:
            self._running = False
        
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        
        self._executor.shutdown(wait=False)
        logger.info("Execution queue stopped")

    def submit(
        self,
        func: Callable,
        *args,
        priority: ExecutionPriority = ExecutionPriority.NORMAL,
        timeout: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Submit a task for execution.

        :param func: Function to execute
        :param args: Positional arguments
        :param priority: Task priority
        :param timeout: Optional timeout override
        :param kwargs: Keyword arguments
        :return: Task ID
        """
        task_id = str(uuid4())
        task = ExecutionTask(
            priority=priority.value,
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            timeout=timeout or self._default_timeout
        )

        try:
            self._queue.put_nowait(task)
            with self._lock:
                self._pending[task_id] = task
                self._total_submitted += 1
            logger.debug(f"Task {task_id} submitted with priority {priority.name}")
            return task_id
        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            raise RuntimeError("Queue is full") from e

    def submit_sync(
        self,
        func: Callable,
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Submit and wait for task completion synchronously.

        :param func: Function to execute
        :param args: Positional arguments
        :param timeout: Optional timeout
        :param kwargs: Keyword arguments
        :return: Task result
        """
        task_id = self.submit(
            func, *args,
            priority=ExecutionPriority.HIGH,
            timeout=timeout,
            **kwargs
        )
        return self.wait_for_result(task_id, timeout=timeout or self._default_timeout)

    def get_result(self, task_id: str) -> Optional[ExecutionResult]:
        """
        Get the result of a completed task.

        :param task_id: The task ID
        :return: ExecutionResult or None if not complete
        """
        with self._lock:
            return self._results.get(task_id)

    def wait_for_result(
        self, 
        task_id: str, 
        timeout: float = 60.0,
        poll_interval: float = 0.1
    ) -> Any:
        """
        Wait for a task to complete and return its result.

        :param task_id: The task ID
        :param timeout: Maximum time to wait
        :param poll_interval: Interval between checks
        :return: Task result
        :raises TimeoutError: If task doesn't complete in time
        :raises RuntimeError: If task failed
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.get_result(task_id)
            if result is not None:
                if result.success:
                    return result.result
                raise RuntimeError(result.error or "Task execution failed")
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")

    def cancel(self, task_id: str) -> bool:
        """
        Cancel a pending task.

        :param task_id: The task ID
        :return: True if cancelled, False if already executing/completed
        """
        with self._lock:
            if task_id in self._pending:
                del self._pending[task_id]
                logger.info(f"Task {task_id} cancelled")
                return True
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self._lock:
            return {
                "running": self._running,
                "queue_size": self._queue.qsize(),
                "max_queue_size": self._max_queue_size,
                "pending_count": len(self._pending),
                "completed_count": len(self._results),
                "total_submitted": self._total_submitted,
                "total_completed": self._total_completed,
                "total_failed": self._total_failed,
                "total_timeouts": self._total_timeouts,
                "resources": self._resource_limiter.get_stats()
            }

    def _worker_loop(self) -> None:
        """Main worker loop that processes tasks from the queue."""
        while self._running:
            try:
                # Get next task with timeout
                try:
                    task = self._queue.get(timeout=0.5)
                except Empty:
                    continue

                # Check if task was cancelled
                with self._lock:
                    if task.task_id not in self._pending:
                        continue

                # Wait for resource availability
                while self._running and not self._resource_limiter.acquire():
                    time.sleep(0.1)

                if not self._running:
                    break

                # Execute the task
                self._execute_task(task)

            except Exception as e:
                logger.error(f"Worker loop error: {e}")

    def _execute_task(self, task: ExecutionTask) -> None:
        """
        Execute a single task.

        :param task: The task to execute
        """
        start_time = time.time()
        queued_time = start_time - task.created_at

        try:
            # Submit to process pool
            future = self._executor.submit(
                task.func, *task.args, **task.kwargs
            )

            # Wait for result with timeout
            result = future.result(timeout=task.timeout)

            execution_time = time.time() - start_time
            exec_result = ExecutionResult(
                task_id=task.task_id,
                success=True,
                result=result,
                execution_time=execution_time,
                queued_time=queued_time
            )

            with self._lock:
                self._results[task.task_id] = exec_result
                self._pending.pop(task.task_id, None)
                self._total_completed += 1

            logger.debug(
                f"Task {task.task_id} completed in {execution_time:.2f}s"
            )

        except TimeoutError:
            execution_time = time.time() - start_time
            exec_result = ExecutionResult(
                task_id=task.task_id,
                success=False,
                error="Task execution timed out",
                execution_time=execution_time,
                queued_time=queued_time
            )

            with self._lock:
                self._results[task.task_id] = exec_result
                self._pending.pop(task.task_id, None)
                self._total_timeouts += 1

            logger.warning(f"Task {task.task_id} timed out")

        except Exception as e:
            execution_time = time.time() - start_time
            exec_result = ExecutionResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                execution_time=execution_time,
                queued_time=queued_time
            )

            with self._lock:
                self._results[task.task_id] = exec_result
                self._pending.pop(task.task_id, None)
                self._total_failed += 1

            logger.error(f"Task {task.task_id} failed: {e}")

        finally:
            self._resource_limiter.release()


# Global execution queue
_global_queue: Optional[ExecutionQueue] = None
_queue_lock = threading.Lock()


def get_execution_queue() -> ExecutionQueue:
    """
    Get or create the global execution queue.

    :return: The global ExecutionQueue instance
    """
    global _global_queue
    if _global_queue is None:
        with _queue_lock:
            if _global_queue is None:
                _global_queue = ExecutionQueue()
                _global_queue.start()
    return _global_queue
