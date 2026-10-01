from flask import Blueprint, g, jsonify, request
from src.controllers import pedido_controller
from src.middlewares.auth import require_role

pedido_bp = Blueprint("pedido", __name__)


@pedido_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    dados = request.get_json(silent=True) or {}
    # usuario_id sempre do token — nunca do corpo (anti-IDOR, T-15)
    resultado = pedido_controller.criar_pedido(g.current_user["id"], dados.get("itens", []))
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@pedido_bp.route("/pedidos", methods=["GET"])
@require_role("admin")
def listar_todos_pedidos():
    return jsonify({"dados": pedido_controller.listar_todos_pedidos(), "sucesso": True}), 200


@pedido_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_controller.listar_pedidos_usuario(g.current_user, usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


@pedido_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
@require_role("admin")
def atualizar_status_pedido(pedido_id):
    dados = request.get_json(silent=True) or {}
    pedido_controller.atualizar_status_pedido(pedido_id, dados.get("status", ""))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
