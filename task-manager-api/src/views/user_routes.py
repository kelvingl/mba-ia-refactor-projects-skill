from flask import Blueprint, request, jsonify, g
from src.controllers import user_controller
from src.schemas.user_schema import CreateUserSchema, UpdateUserSchema, LoginSchema
from src.middlewares.auth import require_role

user_bp = Blueprint('users', __name__)


@user_bp.route('/login', methods=['POST'])
def login():
    payload = LoginSchema().load(request.get_json(silent=True) or {})
    return jsonify(user_controller.login(payload['email'], payload['password'])), 200


@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(user_controller.get_all_users()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify(user_controller.get_user(g.current_user, user_id)), 200


@user_bp.route('/users', methods=['POST'])
@require_role('admin')
def create_user():
    payload = CreateUserSchema().load(request.get_json(silent=True) or {})
    return jsonify(user_controller.create_user(payload)), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    payload = UpdateUserSchema().load(request.get_json(silent=True) or {})
    return jsonify(user_controller.update_user(g.current_user, user_id, payload)), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_role('admin')
def delete_user(user_id):
    return jsonify(user_controller.delete_user(user_id)), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    return jsonify(user_controller.get_user_tasks(g.current_user, user_id)), 200
