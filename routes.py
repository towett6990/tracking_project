from flask import Blueprint

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return "Tracking app is up!"