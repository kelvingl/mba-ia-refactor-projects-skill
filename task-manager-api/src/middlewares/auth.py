from datetime import datetime, timedelta, timezone
from functools import wraps
import jwt
from flask import g, request
from src.config.settings import settings
from src.middlewares.error_handler import UnauthorizedError, ForbiddenError

JWT_ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=24)

# Every new route starts protected; only these endpoints are public.
PUBLIC_ENDPOINTS = frozenset({"index", "health", "users.login"})


def issue_token(user):
    claims = {
        "sub": str(user.id),
        "role": user.role,
        "exp": datetime.now(timezone.utc) + TOKEN_TTL,
    }
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def _authenticate_request():
    if request.method == "OPTIONS":
        return
    endpoint = request.endpoint
    if endpoint is None or endpoint in PUBLIC_ENDPOINTS:
        return
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("Token ausente")
    try:
        claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise UnauthorizedError("Token inválido ou expirado")
    g.current_user = {"id": int(claims["sub"]), "role": claims.get("role")}


def require_role(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if g.current_user.get("role") not in roles:
                raise ForbiddenError("Permissão insuficiente")
            return view(*args, **kwargs)
        return wrapper
    return decorator


def init_auth(app):
    app.before_request(_authenticate_request)
