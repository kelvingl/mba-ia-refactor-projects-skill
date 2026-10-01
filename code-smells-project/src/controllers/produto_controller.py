from src.models import produto_model
from src.middlewares.error_handler import NotFoundError, ValidationError

VALID_CATEGORIES = produto_model.VALID_CATEGORIES


def _validate_produto(dados: dict) -> dict:
    errors = []
    nome = (dados.get("nome") or "").strip()
    if not nome:
        errors.append("Nome é obrigatório")
    elif len(nome) < 2:
        errors.append("Nome muito curto")
    elif len(nome) > 200:
        errors.append("Nome muito longo")

    preco = dados.get("preco")
    if preco is None:
        errors.append("Preço é obrigatório")
    elif not isinstance(preco, (int, float)) or preco < 0:
        errors.append("Preço deve ser número não-negativo")

    estoque = dados.get("estoque")
    if estoque is None:
        errors.append("Estoque é obrigatório")
    elif not isinstance(estoque, (int, float)) or estoque < 0:
        errors.append("Estoque deve ser número não-negativo")

    categoria = dados.get("categoria", "geral")
    if categoria not in VALID_CATEGORIES:
        errors.append(f"Categoria inválida. Válidas: {list(VALID_CATEGORIES)}")

    if errors:
        raise ValidationError("; ".join(errors))

    return {
        "nome": nome,
        "descricao": (dados.get("descricao") or "").strip(),
        "preco": float(preco),
        "estoque": int(estoque),
        "categoria": categoria,
    }


def listar_produtos():
    return produto_model.get_all()


def buscar_produto(produto_id: int):
    produto = produto_model.get_by_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return produto


def buscar_produtos(termo="", categoria=None, preco_min=None, preco_max=None):
    return produto_model.search(termo, categoria, preco_min, preco_max)


def criar_produto(dados: dict) -> dict:
    fields = _validate_produto(dados)
    produto_id = produto_model.create(**fields)
    return {"id": produto_id}


def atualizar_produto(produto_id: int, dados: dict):
    if not produto_model.get_by_id(produto_id):
        raise NotFoundError("Produto não encontrado")
    fields = _validate_produto(dados)
    produto_model.update(produto_id, **fields)


def deletar_produto(produto_id: int):
    if not produto_model.get_by_id(produto_id):
        raise NotFoundError("Produto não encontrado")
    produto_model.delete(produto_id)
