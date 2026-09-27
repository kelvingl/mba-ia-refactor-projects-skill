from flask import Blueprint, jsonify, request
from src.controllers import produto_controller, usuario_controller, pedido_controller, relatorio_controller
from src.models.database import get_db

produto_bp = Blueprint('produtos', __name__)
usuario_bp = Blueprint('usuarios', __name__)
pedido_bp = Blueprint('pedidos', __name__)

@produto_bp.route("/produtos", methods=["GET"])
def listar_produtos():
    produtos = produto_controller.list_all()
    return jsonify({"dados": produtos, "sucesso": True}), 200

@produto_bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)

    resultados = produto_controller.search(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

@produto_bp.route("/produtos/<int:id>", methods=["GET"])
def obter_produto(id):
    produto = produto_controller.get_by_id(id)
    return jsonify({"dados": produto, "sucesso": True}), 200

@produto_bp.route("/produtos", methods=["POST"])
def criar_produto():
    dados = request.get_json() or {}
    produto_id = produto_controller.create(
        dados.get("nome"),
        dados.get("descricao", ""),
        dados.get("preco"),
        dados.get("estoque"),
        dados.get("categoria", "geral")
    )
    return jsonify({"dados": produto_id, "sucesso": True, "mensagem": "Produto criado"}), 201

@produto_bp.route("/produtos/<int:id>", methods=["PUT"])
def atualizar_produto(id):
    dados = request.get_json() or {}
    produto_controller.update(
        id,
        dados.get("nome"),
        dados.get("descricao", ""),
        dados.get("preco"),
        dados.get("estoque"),
        dados.get("categoria", "geral")
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

@produto_bp.route("/produtos/<int:id>", methods=["DELETE"])
def deletar_produto(id):
    produto_controller.delete(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

@usuario_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    usuarios = usuario_controller.list_all()
    return jsonify({"dados": usuarios, "sucesso": True}), 200

@usuario_bp.route("/usuarios/<int:id>", methods=["GET"])
def obter_usuario(id):
    usuario = usuario_controller.get_by_id(id)
    return jsonify({"dados": usuario, "sucesso": True}), 200

@usuario_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    dados = request.get_json() or {}
    usuario_id = usuario_controller.create(
        dados.get("nome"),
        dados.get("email"),
        dados.get("senha")
    )
    return jsonify({"dados": usuario_id, "sucesso": True}), 201

@usuario_bp.route("/login", methods=["POST"])
def login():
    dados = request.get_json() or {}
    usuario = usuario_controller.login(
        dados.get("email"),
        dados.get("senha")
    )
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

@pedido_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    dados = request.get_json() or {}
    resultado = pedido_controller.create(
        dados.get("usuario_id"),
        dados.get("itens", [])
    )
    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso"
    }), 201

@pedido_bp.route("/pedidos", methods=["GET"])
def listar_todos_pedidos():
    pedidos = pedido_controller.get_all()
    return jsonify({"dados": pedidos, "sucesso": True}), 200

@pedido_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_controller.get_by_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200

@pedido_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status_pedido(pedido_id):
    dados = request.get_json() or {}
    pedido_controller.update_status(pedido_id, dados.get("status", ""))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

@produto_bp.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    relatorio = relatorio_controller.relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200

@produto_bp.route("/health", methods=["GET"])
def health_check():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT 1")
    cursor.execute("SELECT COUNT(*) FROM produtos")
    produtos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    usuarios = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    pedidos = cursor.fetchone()[0]

    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": produtos,
            "usuarios": usuarios,
            "pedidos": pedidos
        },
        "versao": "1.0.0",
        "ambiente": "producao"
    }), 200
