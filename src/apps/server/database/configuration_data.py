import sys

sys.path.append(".")


from src.apps.server.database.database import ExecutionManagerDataTable


def parse_config_data():
    return ExecutionManagerDataTable("test.db").retrieve_table()


def update_execution_manager_data(execution_manager_data):

    # Store some test data
    test_data = ExecutionManagerDataTable("test.db")
    test_data.store_data(execution_manager_data)

    # Close the connection when done
    test_data.close()
