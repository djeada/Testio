"""This module defines a Flask blueprint for rendering the index page."""
import sys

sys.path.append(".")
from flask import Blueprint, render_template
from src.apps.server.database.configuration_data import parse_config_data

index_page_blueprint: Blueprint = Blueprint("index_page", __name__)


@index_page_blueprint.route("/")
def index_page() -> str:
    """Renders the index page and passes the configuration data to the template.

    :return: The HTML content of the index page.
    """
    config_data = parse_config_data()
    return render_template("index.html", config_data=config_data)
