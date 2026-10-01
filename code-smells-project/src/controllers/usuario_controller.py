from src.models import usuario_model
from src.middlewares.auth import issue_token
from src.middlewares.error_handler import (
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


def _ensure_self_or_admin(current_user: dict, owner_id: int):
    if current_user["role"] != "admin" and current_user["id"] != owner_id:
        raise ForbiddenError("Acesso a recurso de outro usuário")


def listar_usuarios():
    return usuario_model.get_all()


def buscar_usuario(current_user: dict, usuario_id: int):
    _ensure_self_or_admin(current_user, usuario_id)
    usuario = usuario_model.get_by_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar_usuario(dados: dict) -> dict:
    nome = (dados.get("nome") or "").strip()
    email = (dados.get("email") or "").strip()
    senha = dados.get("senha", "")
    tipo = dados.get("tipo", "cliente")

    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")

    usuario_id = usuario_model.create(nome, email, senha, tipo)
    return {"id": usuario_id}


def login(dados: dict) -> dict:
    email = (dados.get("email") or "").strip()
    senha = dados.get("senha", "")

    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    usuario = usuario_model.authenticate(email, senha)
    if not usuario:
        raise UnauthorizedError("Email ou senha inválidos")

    token = issue_token(usuario)
    return {
        "usuario": {"id": usuario["id"], "nome": usuario["nome"], "email": usuario["email"]},
        "token": token,
    }
