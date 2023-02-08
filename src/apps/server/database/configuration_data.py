import dataclasses


@dataclasses.dataclass
class GlobalConfiguration:
    execution_manager_data = None


global_config = GlobalConfiguration()

global_test_suite_data = (
    None  # TODO: This is just a quick and dirty fix to get the information I need.
)


def parse_config_data():
    global global_config
    return global_config.execution_manager_data


def update_execution_manager_data(execution_manager_data):
    global global_config
    global_config.execution_manager_data = execution_manager_data
    parse_config_data()
