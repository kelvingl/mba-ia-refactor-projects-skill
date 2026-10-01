import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from models.database import db
from models.user import User
from models.task import Task
from middlewares.error_handler import (
    NotFoundError, ConflictError, ForbiddenError, UnauthorizedError
)

logger = logging.getLogger(__name__)

_PRIVILEGED_FIELDS = frozenset({"role", "active"})


def _ensure_self_or_admin(current_user, target_id):
    if current_user["role"] != "admin" and current_user["id"] != target_id:
        raise ForbiddenError("Acesso a recurso de outro usuário")


def _ensure_can_set_fields(current_user, payload):
    if current_user["role"] != "admin" and _PRIVILEGED_FIELDS & payload.keys():
        raise ForbiddenError("Somente admin pode alterar papel ou status")


def get_all_users():
    users = User.query.options(joinedload(User.tasks)).all()
    return [{**u.to_dict(), "task_count": len(u.tasks)} for u in users]


def get_user(current_user, user_id):
    _ensure_self_or_admin(current_user, user_id)
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    data = user.to_dict()
    data["tasks"] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return data


def create_user(current_user, payload):
    if User.query.filter_by(email=payload["email"]).first():
        raise ConflictError("Email já cadastrado")
    user = User(name=payload["name"], email=payload["email"], role=payload.get("role", "user"))
    user.set_password(payload["password"])
    try:
        db.session.add(user)
        db.session.commit()
        logger.info("Usuário criado: %d - %s", user.id, user.name)
        return user.to_dict()
    except SQLAlchemyError:
        db.session.rollback()
        raise


def update_user(current_user, user_id, payload):
    _ensure_self_or_admin(current_user, user_id)
    _ensure_can_set_fields(current_user, payload)
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    if "email" in payload:
        existing = User.query.filter_by(email=payload["email"]).first()
        if existing and existing.id != user_id:
            raise ConflictError("Email já cadastrado")
        user.email = payload["email"]
    if "name" in payload:
        user.name = payload["name"]
    if "password" in payload:
        user.set_password(payload["password"])
    if "role" in payload and current_user["role"] == "admin":
        user.role = payload["role"]
    if "active" in payload and current_user["role"] == "admin":
        user.active = payload["active"]
    try:
        db.session.commit()
        return user.to_dict()
    except SQLAlchemyError:
        db.session.rollback()
        raise


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    try:
        db.session.delete(user)
        db.session.commit()
        logger.info("Usuário deletado: %d", user_id)
    except SQLAlchemyError:
        db.session.rollback()
        raise


def get_user_tasks(current_user, user_id):
    _ensure_self_or_admin(current_user, user_id)
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    return [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]


def login(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise UnauthorizedError("Credenciais inválidas")
    if not user.active:
        raise ForbiddenError("Usuário inativo")
    return user
