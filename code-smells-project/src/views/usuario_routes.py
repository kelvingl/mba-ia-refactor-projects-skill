from flask import Blueprint, g, jsonify, request
from src.controllers import usuario_controller
from src.middlewares.auth import require_role

usuario_bp = Blueprint("usuario", __name__)


@usuario_bp.route("/login", methods=["POST"])
def login():
    dados = request.get_json(silent=True) or {}
    resultado = usuario_controller.login(dados)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Login OK"}), 200


@usuario_bp.route("/usuarios", methods=["GET"])
@require_role("admin")
def listar_usuarios():
    return jsonify({"dados": usuario_controller.listar_usuarios(), "sucesso": True}), 200


@usuario_bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id):
    return jsonify({
        "dados": usuario_controller.buscar_usuario(g.current_user, usuario_id),
        "sucesso": True,
    }), 200


@usuario_bp.route("/usuarios", methods=["POST"])
@require_role("admin")
def criar_usuario():
    dados = request.get_json(silent=True) or {}
    resultado = usuario_controller.criar_usuario(dados)
    return jsonify({"dados": resultado, "sucesso": True}), 201
