import sys

sys.path.append(".")
from flask import Blueprint, render_template

from src.apps.server.database.configuration_data import parse_config_data

homework_mode_page_blueprint = Blueprint("homework_mode_page", __name__)


@homework_mode_page_blueprint.route("/homework")
def homework_mode_page():
    # Pass the config data to the template, so the web page has access to it.
    return render_template("homework_mode.html", config_data=parse_config_data())
