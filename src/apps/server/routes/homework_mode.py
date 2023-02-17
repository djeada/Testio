"""This module defines a Flask blueprint for rendering the homework mode web page."""
import sys

sys.path.append(".")

from flask import Blueprint, render_template
from src.apps.server.database.configuration_data import parse_config_data

homework_mode_page_blueprint: Blueprint = Blueprint("homework_mode_page", __name__)


@homework_mode_page_blueprint.route("/homework")
def homework_mode_page() -> str:
    """Renders a web page for the homework mode and passes the configuration data to the template.

    :return: The HTML content of the homework mode web page.
    """
    config_data = parse_config_data()
    return render_template("homework_mode.html", config_data=config_data)
