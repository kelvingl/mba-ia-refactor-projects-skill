from src.models import pedido_model, usuario_model
from src.middlewares.error_handler import NotFoundError, ValidationError

VALID_STATUSES = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

def create(usuario_id, itens):
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    usuario = usuario_model.get_by_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")

    resultado = pedido_model.create(usuario_id, itens)
    if "erro" in resultado:
        raise ValidationError(resultado["erro"])

    return resultado

def get_by_usuario(usuario_id):
    usuario = usuario_model.get_by_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")

    return pedido_model.get_by_usuario(usuario_id)

def get_all():
    return pedido_model.get_all()

def update_status(pedido_id, novo_status):
    if novo_status not in VALID_STATUSES:
        raise ValidationError(f"Status inválido. Válidos: {VALID_STATUSES}")

    pedido_model.update_status(pedido_id, novo_status)
    return True
