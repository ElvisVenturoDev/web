from flask import Blueprint, render_template

from app.services.product_service import load_products

HOME_BP = Blueprint("home", __name__)


@HOME_BP.get("/")
def index():
    """Show the home page with the featured rooms.

    Returns:
        str: HTML of the home page.
    """
    rooms = [room for room in load_products() if room.get("featured")][:3]
    return render_template("home/index.html", rooms=rooms)
