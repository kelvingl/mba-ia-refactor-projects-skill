from src.models import produto_model
from src.middlewares.error_handler import NotFoundError, ValidationError

VALID_CATEGORIES = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]

def list_all():
    return produto_model.get_all()

def get_by_id(produto_id):
    produto = produto_model.get_by_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return produto

def create(nome, descricao, preco, estoque, categoria):
    if not nome or len(nome) < 2 or len(nome) > 200:
        raise ValidationError("Nome inválido")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if categoria not in VALID_CATEGORIES:
        raise ValidationError(f"Categoria inválida. Válidas: {VALID_CATEGORIES}")

    produto_id = produto_model.create(nome, descricao, preco, estoque, categoria)
    return {"id": produto_id}

def update(produto_id, nome, descricao, preco, estoque, categoria):
    produto = produto_model.get_by_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")

    if not nome or len(nome) < 2 or len(nome) > 200:
        raise ValidationError("Nome inválido")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")

    produto_model.update(produto_id, nome, descricao, preco, estoque, categoria)
    return True

def delete(produto_id):
    produto = produto_model.get_by_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")

    produto_model.delete(produto_id)
    return True

def search(termo=None, categoria=None, preco_min=None, preco_max=None):
    return produto_model.search(termo, categoria, preco_min, preco_max)
