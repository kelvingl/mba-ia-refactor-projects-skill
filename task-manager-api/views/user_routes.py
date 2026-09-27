from flask import Blueprint, request, jsonify
import controllers.user_controller as user_ctrl
from schemas.user_schema import CreateUserSchema, UpdateUserSchema
from middlewares.error_handler import BadRequestError

user_bp = Blueprint('users', __name__)

_create_schema = CreateUserSchema()
_update_schema = UpdateUserSchema()


@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(user_ctrl.get_all_users()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify(user_ctrl.get_user_by_id(user_id)), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    payload = _create_schema.load(request.get_json(silent=True) or {})
    return jsonify(user_ctrl.create_user(payload)), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    payload = _update_schema.load(request.get_json(silent=True) or {})
    return jsonify(user_ctrl.update_user(user_id, payload)), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user_ctrl.delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    return jsonify(user_ctrl.get_user_tasks(user_id)), 200


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    if not data.get('email') or not data.get('password'):
        raise BadRequestError('Email e senha são obrigatórios')
    return jsonify(user_ctrl.login(data['email'], data['password'])), 200
