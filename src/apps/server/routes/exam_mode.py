"""This module defines a Flask blueprint for the exam mode page."""
import sys

sys.path.append(".")
from flask import Blueprint, render_template

exam_mode_page_blueprint = Blueprint("exam_mode_page", __name__)


@exam_mode_page_blueprint.route("/exam")
def exam_mode_page() -> str:
    """Renders the exam mode page.

    :return: The rendered HTML for the exam mode page.
    """
    return render_template("exam_mode.html")
