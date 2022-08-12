from flask import Flask
from flask_cors import CORS

from .database.models import setup_db

app = Flask(__name__)
setup_db(app)
CORS(app, resources={r"/*": {"origins": "*"}})