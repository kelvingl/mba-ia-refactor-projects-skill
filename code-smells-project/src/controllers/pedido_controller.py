from src.models import pedido_model
from src.middlewares.error_handler import ForbiddenError, ValidationError

VALID_STATUSES = ("pendente", "aprovado", "enviado", "entregue", "cancelado")


def _ensure_self_or_admin(current_user: dict, owner_id: int):
    if current_user["role"] != "admin" and current_user["id"] != owner_id:
        raise ForbiddenError("Acesso a recurso de outro usuário")


def criar_pedido(current_user_id: int, itens: list) -> dict:
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    resultado = pedido_model.create(current_user_id, itens)
    if "erro" in resultado:
        raise ValidationError(resultado["erro"])
    return resultado


def listar_todos_pedidos() -> list:
    return pedido_model.get_all()


def listar_pedidos_usuario(current_user: dict, usuario_id: int) -> list:
    _ensure_self_or_admin(current_user, usuario_id)
    return pedido_model.get_by_usuario(usuario_id)


def atualizar_status_pedido(pedido_id: int, novo_status: str):
    if novo_status not in VALID_STATUSES:
        raise ValidationError(f"Status inválido. Válidos: {list(VALID_STATUSES)}")
    pedido_model.update_status(pedido_id, novo_status)
