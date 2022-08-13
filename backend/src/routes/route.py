import json
import os
from urllib.parse import urlencode, quote_plus

from authlib.integrations.flask_client import OAuth
from flask import jsonify, abort, request, session, redirect, url_for
from sqlalchemy import exc

from .. import app
from ..auth.auth import requires_auth
from ..database.models import Drink
from dotenv import load_dotenv

load_dotenv("../auth/.env")
app.secret_key = os.environ.get("APP_SECRET_KEY")
oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=os.environ.get("AUTH0_CLIENT_ID"),
    client_secret=os.environ.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


@app.route('/')
def index():
    return jsonify({
        'success': True,
        'message': 'Welcome to the drinks API'
    })


@app.route("/drinks")
def get_drinks():
    drinks = Drink.query.all()
    drinks_short = [drink.short() for drink in drinks]
    return jsonify({"success": True, "drinks": drinks_short})


@app.route("/drinks-detail")
@requires_auth("get:drinks-detail")
def get_drinks_detail():
    drinks = Drink.query.all()
    drinks_long = [drink.long() for drink in drinks]
    return jsonify({"success": True, "drinks": drinks_long})


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def create_drink():
    body = request.get_json()
    if body is None:
        abort(400, "No JSON body found")
    try:
        drink = Drink(title=body.get("title"), recipe=json.dumps(body.get("recipe")))
        drink.insert()
        return jsonify({"success": True, "drinks": [drink.long()]})
    except exc.IntegrityError:
        abort(400, "Drink already exists")


@app.route('/drinks/<int:id_drink>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(id_drink):
    drink = Drink.query.filter_by(id=id_drink).one_or_none()
    if drink is None:
        abort(404)
    body = request.get_json()
    if body is None:
        abort(400)
    try:
        drink.title = body.get("title")
        drink.recipe = json.dumps(body.get("recipe"))
        drink.update()
        return jsonify({"success": True, "drinks": [drink.long()]})
    except exc.IntegrityError:
        abort(400)


@app.route("/drinks/<int:id_drink>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(id_drink):
    drink = Drink.query.filter_by(id=id_drink).one_or_none()
    if drink is None:
        abort(404, "Drink not found")
    drink.delete()
    return jsonify({"success": True, "delete": id_drink})


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("http://localhost:8100/tabs/user-page")


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + os.environ.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": "http://localhost:8100/tabs/user-page",
                "client_id": os.environ.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )
