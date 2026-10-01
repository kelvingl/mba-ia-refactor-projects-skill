import logging
from src.models.database import db
from src.models.user import User
from src.models.task import Task
from src.middlewares.error_handler import NotFoundError, ConflictError, UnauthorizedError, ForbiddenError
from src.controllers.authorization import ensure_self_or_admin, ensure_can_set_fields

logger = logging.getLogger(__name__)

UPDATABLE_FIELDS = ("name", "email", "role", "active")


def get_all_users():
    users = User.query.all()
    return [{**u.to_dict(), 'task_count': len(u.tasks)} for u in users]


def get_user(current_user, user_id):
    ensure_self_or_admin(current_user, user_id)
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return data


def create_user(payload):
    if User.query.filter_by(email=payload['email']).first():
        raise ConflictError("Email já cadastrado")
    user = User()
    user.name = payload['name']
    user.email = payload['email']
    user.set_password(payload['password'])
    user.role = payload.get('role', 'user')
    db.session.add(user)
    db.session.commit()
    logger.info("User created: %d %s", user.id, user.name)
    return user.to_dict()


def update_user(current_user, user_id, payload):
    ensure_self_or_admin(current_user, user_id)
    ensure_can_set_fields(current_user, payload)
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    for field in UPDATABLE_FIELDS:
        if field in payload:
            setattr(user, field, payload[field])
    if 'password' in payload:
        user.set_password(payload['password'])
    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    Task.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    logger.info("User deleted: %d", user_id)
    return {'message': 'Usuário deletado com sucesso'}


def get_user_tasks(current_user, user_id):
    ensure_self_or_admin(current_user, user_id)
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    tasks = Task.query.filter_by(user_id=user_id).all()
    return [{**t.to_dict(), 'overdue': t.is_overdue()} for t in tasks]


def login(email, password):
    from src.middlewares.auth import issue_token
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise UnauthorizedError("Credenciais inválidas")
    if not user.active:
        raise ForbiddenError("Usuário inativo")
    token = issue_token(user)
    return {'message': 'Login realizado com sucesso', 'user': user.to_dict(), 'token': token}
