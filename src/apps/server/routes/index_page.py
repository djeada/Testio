import sys

sys.path.append(".")
from flask import Blueprint, render_template

from src.apps.server.database.configuration_data import parse_config_data

index_page_blueprint = Blueprint("index_page", __name__)


@index_page_blueprint.route("/")
def index_page():
    # Pass the config data to the template, so the web page has access to it.
    return render_template("index.html", config_data=parse_config_data())
