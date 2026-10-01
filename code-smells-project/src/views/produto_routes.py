from flask import Blueprint, jsonify, request
from src.controllers import produto_controller
from src.middlewares.auth import require_role

produto_bp = Blueprint("produto", __name__)


@produto_bp.route("/produtos", methods=["GET"])
def listar_produtos():
    return jsonify({"dados": produto_controller.listar_produtos(), "sucesso": True}), 200


@produto_bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    preco_min_raw = request.args.get("preco_min")
    preco_max_raw = request.args.get("preco_max")
    preco_min = float(preco_min_raw) if preco_min_raw else None
    preco_max = float(preco_max_raw) if preco_max_raw else None
    resultados = produto_controller.buscar_produtos(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


@produto_bp.route("/produtos/<int:produto_id>", methods=["GET"])
def buscar_produto(produto_id):
    return jsonify({"dados": produto_controller.buscar_produto(produto_id), "sucesso": True}), 200


@produto_bp.route("/produtos", methods=["POST"])
@require_role("admin")
def criar_produto():
    dados = request.get_json(silent=True) or {}
    resultado = produto_controller.criar_produto(dados)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Produto criado"}), 201


@produto_bp.route("/produtos/<int:produto_id>", methods=["PUT"])
@require_role("admin")
def atualizar_produto(produto_id):
    dados = request.get_json(silent=True) or {}
    produto_controller.atualizar_produto(produto_id, dados)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@produto_bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
@require_role("admin")
def deletar_produto(produto_id):
    produto_controller.deletar_produto(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
