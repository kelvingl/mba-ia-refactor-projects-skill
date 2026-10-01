from flask import Blueprint, jsonify, request, g
from marshmallow import ValidationError as MarshmallowValidationError
from middlewares.error_handler import ValidationError, ForbiddenError
from middlewares.auth import issue_token, require_role
import controllers.user_controller as user_controller
from schemas.user_schema import CreateUserSchema, UpdateUserSchema, AdminUpdateUserSchema

user_bp = Blueprint("users", __name__)

_create_schema = CreateUserSchema()
_update_schema = UpdateUserSchema()
_admin_update_schema = AdminUpdateUserSchema()


@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise ValidationError("Email e senha são obrigatórios")
    user = user_controller.login(email, password)
    return jsonify({
        "message": "Login realizado com sucesso",
        "user": user.to_dict(),
        "token": issue_token(user),
    }), 200


@user_bp.route("/users", methods=["GET"])
def get_users():
    return jsonify(user_controller.get_all_users()), 200


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return jsonify(user_controller.get_user(g.current_user, user_id)), 200


@user_bp.route("/users", methods=["POST"])
@require_role("admin")
def create_user():
    try:
        payload = _create_schema.load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as e:
        raise ValidationError(str(e.messages))
    return jsonify(user_controller.create_user(g.current_user, payload)), 201


_PRIVILEGED_FIELDS = frozenset({"role", "active"})


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    raw = request.get_json(silent=True) or {}
    # Verifica campos de privilégio ANTES da validação de schema (evita 400 silencioso)
    if g.current_user["role"] != "admin" and _PRIVILEGED_FIELDS & raw.keys():
        raise ForbiddenError("Somente admin pode alterar papel ou status")
    schema = _admin_update_schema if g.current_user["role"] == "admin" else _update_schema
    try:
        payload = schema.load(raw)
    except MarshmallowValidationError as e:
        raise ValidationError(str(e.messages))
    return jsonify(user_controller.update_user(g.current_user, user_id, payload)), 200


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@require_role("admin")
def delete_user(user_id):
    user_controller.delete_user(user_id)
    return jsonify({"message": "Usuário deletado com sucesso"}), 200


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
def get_user_tasks(user_id):
    return jsonify(user_controller.get_user_tasks(g.current_user, user_id)), 200
