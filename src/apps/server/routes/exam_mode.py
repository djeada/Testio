import sys

sys.path.append(".")
from flask import Blueprint, render_template

from src.apps.server.database.configuration_data import parse_config_data

exam_mode_page_blueprint = Blueprint("exam_mode_page", __name__)


@exam_mode_page_blueprint.route("/exam")
def exam_mode_page():
    # Pass the config data to the template, so the web page has access to it.
    return render_template("exam_mode.html", config_data=parse_config_data())
