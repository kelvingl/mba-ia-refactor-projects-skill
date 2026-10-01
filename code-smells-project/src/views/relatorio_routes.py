from flask import Blueprint, jsonify
from src.controllers import relatorio_controller
from src.middlewares.auth import require_role

relatorio_bp = Blueprint("relatorio", __name__)


@relatorio_bp.route("/relatorios/vendas", methods=["GET"])
@require_role("admin")
def relatorio_vendas():
    return jsonify({"dados": relatorio_controller.relatorio_vendas(), "sucesso": True}), 200
