from .database.models import db_drop_and_create_all
from . import app
from .routes.route import index, create_drink, get_drinks, get_drinks_detail, update_drink, delete_drink
from .errors.error import forbidden, unauthorized, not_found, bad_request, server_error, unprocessable


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
    return response


db_drop_and_create_all()

# ROUTES


if __name__ == '__main__':
    app.run(debug=True)
