from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, request

from src.config.settings import settings
from src.middlewares.error_handler import ForbiddenError, UnauthorizedError

JWT_ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=24)

# Rotas acessíveis sem token. Toda rota nova nasce protegida — adicione aqui apenas rotas verdadeiramente públicas.
PUBLIC_ENDPOINTS = frozenset({
    "static",
    "health.index",
    "health.health_check",
    "usuario.login",
    "produto.listar_produtos",
    "produto.buscar_produtos",
    "produto.buscar_produto",
})


def issue_token(user: dict) -> str:
    claims = {
        "sub": str(user["id"]),
        "role": user["tipo"],
        "exp": datetime.now(timezone.utc) + TOKEN_TTL,
    }
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def authenticate_request():
    if request.method == "OPTIONS":
        return
    if request.endpoint is None or request.endpoint in PUBLIC_ENDPOINTS:
        return
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("Token ausente ou formato inválido")
    try:
        claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise UnauthorizedError("Token inválido ou expirado")
    g.current_user = {"id": int(claims["sub"]), "role": claims.get("role", "cliente")}


def require_role(*roles: str):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if g.current_user.get("role") not in roles:
                raise ForbiddenError("Permissão insuficiente")
            return view(*args, **kwargs)
        return wrapper
    return decorator


def init_auth(app):
    app.before_request(authenticate_request)
