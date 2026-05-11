"""Configuration data persistence using the config database (test.db by default).

Note: The server uses two separate databases:
  - config DB (TESTIO_CONFIG_DB_PATH, default "test.db")  — stores test-suite configs
  - app DB    (TESTIO_APP_DB_PATH,    default "testio.db") — stores exam sessions, submissions
This is intentional: configuration and runtime data have different lifecycles.
"""

from src.apps.server.database.database import ExecutionManagerDataTable
from src.apps.server.settings import get_config_database_path
from src.core.caching.memory_cache import cache_result, get_global_cache

_PARSE_CONFIG_CACHE_KEY = "parse_config_data"


@cache_result(ttl=30.0, key_prefix=_PARSE_CONFIG_CACHE_KEY)
def parse_config_data():
    """Retrieve all test-suite configurations from the config database.

    Results are cached for 30 seconds. The cache is invalidated automatically
    when ``update_execution_manager_data`` writes new configuration.
    """
    return ExecutionManagerDataTable(get_config_database_path()).retrieve_table()


def update_execution_manager_data(execution_manager_data):
    # Store some test data
    test_data = ExecutionManagerDataTable(get_config_database_path())
    test_data.store_data(execution_manager_data)
    test_data.close()

    # Invalidate the parse_config_data cache so subsequent reads see the new data
    get_global_cache().delete(_PARSE_CONFIG_CACHE_KEY)
