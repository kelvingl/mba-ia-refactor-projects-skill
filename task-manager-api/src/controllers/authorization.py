from src.middlewares.error_handler import ForbiddenError

PRIVILEGED_USER_FIELDS = frozenset({"role", "active"})


def is_admin(current_user):
    return current_user.get("role") == "admin"


def ensure_self_or_admin(current_user, owner_id):
    if not is_admin(current_user) and current_user["id"] != owner_id:
        raise ForbiddenError("Acesso a recurso de outro usuário")


def ensure_can_set_fields(current_user, payload, privileged=PRIVILEGED_USER_FIELDS):
    if not is_admin(current_user) and privileged & payload.keys():
        raise ForbiddenError("Somente admin pode alterar papel ou status")
