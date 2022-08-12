import json

from flask import jsonify, abort, request
from sqlalchemy import exc

from .. import app
from ..auth.auth import requires_auth
from ..database.models import Drink


@app.route('/')
def index():
    return jsonify({
        'success': True,
        'message': 'Welcome to the drinks API'
    })


@app.route("/drinks")
@requires_auth("get:drinks")
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
        abort(400)
    try:
        drink = Drink(title=body.get("title"), recipe=json.dumps(body.get("recipe")))
        drink.insert()
        return jsonify({"success": True, "drinks": [drink.long()]})
    except exc.IntegrityError:
        abort(400)


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
        abort(404)
    drink.delete()
    return jsonify({"success": True, "delete": id_drink})
