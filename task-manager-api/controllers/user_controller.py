import logging
from datetime import datetime, timezone, timedelta
import jwt
from models.database import db
from models.user import User
from middlewares.error_handler import NotFoundError, ConflictError, UnauthorizedError, ForbiddenError
from config.settings import settings

logger = logging.getLogger('app')


def get_all_users():
    from sqlalchemy.orm import subqueryload
    users = User.query.options(subqueryload(User.tasks)).all()
    result = []
    for u in users:
        data = u.to_dict()
        data['task_count'] = len(u.tasks)
        result.append(data)
    return result


def get_user_by_id(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in user.tasks]
    return data


def create_user(payload):
    if User.query.filter_by(email=payload['email']).first():
        raise ConflictError('Email já cadastrado')
    user = User(name=payload['name'], email=payload['email'], role=payload.get('role', 'user'))
    user.set_password(payload['password'])
    db.session.add(user)
    db.session.commit()
    logger.info('User created: %d - %s', user.id, user.name)
    return user.to_dict()


def update_user(user_id, payload):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    if 'email' in payload:
        existing = User.query.filter_by(email=payload['email']).first()
        if existing and existing.id != user_id:
            raise ConflictError('Email já cadastrado')
        user.email = payload['email']

    if 'name' in payload:
        user.name = payload['name']
    if 'password' in payload:
        user.set_password(payload['password'])
    if 'role' in payload:
        user.role = payload['role']
    if 'active' in payload:
        user.active = payload['active']

    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    db.session.delete(user)
    db.session.commit()
    logger.info('User deleted: %d', user_id)


def get_user_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return [t.to_dict() for t in user.tasks]


def login(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    token = jwt.encode(
        {'user_id': user.id, 'role': user.role,
         'exp': datetime.now(timezone.utc) + timedelta(hours=24)},
        settings.SECRET_KEY,
        algorithm='HS256',
    )
    return {'message': 'Login realizado com sucesso', 'user': user.to_dict(), 'token': token}
