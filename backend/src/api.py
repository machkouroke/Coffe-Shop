import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
    return response


# db_drop_and_create_all()

# ROUTES
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


@app.route("/drinks/<int:id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(id_drink):
    drink = Drink.query.filter_by(id=id_drink).one_or_none()
    if drink is None:
        abort(404)
    drink.delete()
    return jsonify({"success": True, "delete": id_drink})


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": f"unprocessable: {error.description}"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": f"Not found: {error.description}"
    }), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": f"Bad request: {error.description}"
    }), 400


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Internal server error"
    }), 500


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": f"Unauthorized: {error.description}"
    }), 401


@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": f"Forbidden: {error.description}"
    }), 403


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code


if __name__ == '__main__':
    app.run(debug=True)
