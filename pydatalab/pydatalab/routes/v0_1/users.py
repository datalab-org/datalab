from flask import Blueprint, jsonify, request
from flask_login import current_user
from bson import ObjectId

from pydatalab.mongo import flask_mongo

user = Blueprint("users", __name__)


@user.route('/users/<user_id>', methods=['PATCH'])
def save_user(user_id):
    
    user_name = request.json.get('data', {}).get('user_name')

    user_id_object = ObjectId(user_id)
    flask_mongo.db.users.update_one({"_id": user_id_object}, {'$set': {'display_name': user_name}})

    return jsonify(status="success"), 200


