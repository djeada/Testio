"""Configuration data persistence using the config database (test.db by default).

Note: The server uses two separate databases:
  - config DB (TESTIO_CONFIG_DB_PATH, default "test.db")  — stores test-suite configs
  - app DB    (TESTIO_APP_DB_PATH,    default "testio.db") — stores exam sessions, submissions
This is intentional: configuration and runtime data have different lifecycles.

Reads are cached in-process for a short time; writes through this module
invalidate the cache of the current process. Other worker processes pick up
changes when their cache entry expires (at most the TTL below).
"""

from typing import Any, Dict, Optional

from testio.apps.server.database.database import ExecutionManagerDataTable
from testio.apps.server.settings import get_config_database_path
from testio.core.caching.memory_cache import cache_result

_PARSE_CONFIG_CACHE_KEY = "parse_config_data"
_SUITE_CONFIG_CACHE_KEY = "suite_config_data"
_CACHE_TTL_SECONDS = 30.0


@cache_result(ttl=_CACHE_TTL_SECONDS, key_prefix=_PARSE_CONFIG_CACHE_KEY)
def parse_config_data():
    """Retrieve all test-suite configurations from the config database.

    Results are cached for 30 seconds. The cache is invalidated automatically
    when ``update_execution_manager_data`` writes new configuration.
    """
    return ExecutionManagerDataTable(get_config_database_path()).retrieve_table()


@cache_result(ttl=_CACHE_TTL_SECONDS, key_prefix=_SUITE_CONFIG_CACHE_KEY)
def load_suite_config_json() -> Optional[Dict[str, Any]]:
    """The raw test-suite config last loaded by the teacher, if any."""
    return ExecutionManagerDataTable(get_config_database_path()).retrieve_suite_config()


def update_execution_manager_data(execution_manager_data):
    # Store some test data
    test_data = ExecutionManagerDataTable(get_config_database_path())
    test_data.store_data(execution_manager_data)
    test_data.close()

    # Invalidate the parse_config_data cache so subsequent reads see the new
    # data (the decorator knows the exact key it caches under).
    parse_config_data.invalidate()


def update_suite_config(config_json: Dict[str, Any]) -> None:
    """Persist the raw (already validated) test-suite config."""
    ExecutionManagerDataTable(get_config_database_path()).store_suite_config(
        config_json
    )
    load_suite_config_json.invalidate()
