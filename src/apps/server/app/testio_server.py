import sys

from flask import Flask

sys.path.append(".")
from src.apps.server.routes.execute_tests import execute_tests_blueprint
from src.apps.server.routes.index_page import index_page_blueprint
from src.apps.server.routes.update_test_suite import update_test_suite_blueprint


class TestioServer(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create all the routes
        routes = [
            index_page_blueprint,
            update_test_suite_blueprint,
            execute_tests_blueprint,
        ]

        for route in routes:
            self.register_blueprint(route)
