from src.models import usuario_model
from src.middlewares.error_handler import NotFoundError, ValidationError

def list_all():
    return usuario_model.get_all()

def get_by_id(usuario_id):
    usuario = usuario_model.get_by_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return usuario

def create(nome, email, senha):
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")

    usuario_id = usuario_model.create(nome, email, senha)
    return {"id": usuario_id}

def login(email, senha):
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    usuario = usuario_model.login(email, senha)
    if not usuario:
        raise ValidationError("Email ou senha inválidos")

    return usuario
