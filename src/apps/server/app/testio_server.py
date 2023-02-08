"""A custom Flask application for the TestioServer."""
import sys

sys.path.append(".")

from flask import Flask

from src.apps.server.database.database import Database
from src.apps.server.routes.execute_tests import execute_tests_blueprint
from src.apps.server.routes.index_page import index_page_blueprint
from src.apps.server.routes.update_test_suite import update_test_suite_blueprint


class TestioServer(Flask):
    """A custom Flask application for the TestioServer."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the TestioServer and its routes.

        :param args: Positional arguments to pass to the parent class.
        :param kwargs: Keyword arguments to pass to the parent class.
        """
        super().__init__(*args, **kwargs)
        # Reference to the custom database class
        self.db = Database("testio.db")

        # create all the routes
        routes = [
            index_page_blueprint,
            update_test_suite_blueprint,
            execute_tests_blueprint,
        ]

        for route in routes:
            self.register_blueprint(route)
