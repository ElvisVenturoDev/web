from flask import Blueprint, render_template

ABOUT_BP = Blueprint("about", __name__)


@ABOUT_BP.get("/nosotros")
def about():
    """Show the about module index.

    Returns:
        str: HTML of the about index page.
    """
    return render_template("about/index.html")


@ABOUT_BP.get("/nosotros/historia")
def about_detail():
    """Show the full company story.

    Returns:
        str: HTML of the about detail page.
    """
    return render_template("about/about.html")
