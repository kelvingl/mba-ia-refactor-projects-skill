from src.models.database import get_db

_PEDIDO_JOIN = """
    SELECT p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
           ip.produto_id, ip.quantidade, ip.preco_unitario,
           pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
"""


def _build_pedidos(rows):
    pedidos: dict = {}
    for r in rows:
        pid = r["pedido_id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid,
                "usuario_id": r["usuario_id"],
                "status": r["status"],
                "total": r["total"],
                "criado_em": r["criado_em"],
                "itens": [],
            }
        if r["produto_id"] is not None:
            pedidos[pid]["itens"].append({
                "produto_id": r["produto_id"],
                "produto_nome": r["produto_nome"] or "Desconhecido",
                "quantidade": r["quantidade"],
                "preco_unitario": r["preco_unitario"],
            })
    return list(pedidos.values())


def get_all():
    rows = get_db().execute(_PEDIDO_JOIN + " ORDER BY p.id").fetchall()
    return _build_pedidos(rows)


def get_by_usuario(usuario_id):
    rows = get_db().execute(
        _PEDIDO_JOIN + " WHERE p.usuario_id = ? ORDER BY p.id", (usuario_id,)
    ).fetchall()
    return _build_pedidos(rows)


def create(usuario_id, itens):
    db = get_db()
    total = 0.0
    produtos_preco: dict = {}

    for item in itens:
        row = db.execute(
            "SELECT id, preco, estoque, nome FROM produtos WHERE id = ? AND ativo = 1",
            (item["produto_id"],),
        ).fetchone()
        if row is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if row["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {row['nome']}"}
        total += row["preco"] * item["quantidade"]
        produtos_preco[item["produto_id"]] = row["preco"]

    pedido_id = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    ).lastrowid

    for item in itens:
        db.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)"
            " VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], produtos_preco[item["produto_id"]]),
        )
        db.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )

    db.commit()
    return {"pedido_id": pedido_id, "total": total}


def update_status(pedido_id, novo_status):
    db = get_db()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
