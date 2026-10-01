from src.models.database import get_db

VALID_CATEGORIES = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")


def _row_to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": bool(row["ativo"]),
        "criado_em": row["criado_em"],
    }


def get_all():
    rows = get_db().execute("SELECT * FROM produtos WHERE ativo = 1").fetchall()
    return [_row_to_dict(r) for r in rows]


def get_by_id(produto_id):
    row = get_db().execute(
        "SELECT * FROM produtos WHERE id = ? AND ativo = 1", (produto_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def search(termo="", categoria=None, preco_min=None, preco_max=None):
    conditions, params = ["ativo = 1"], []
    if termo:
        conditions.append("(nome LIKE ? OR descricao LIKE ?)")
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        conditions.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        conditions.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        conditions.append("preco <= ?")
        params.append(preco_max)
    query = f"SELECT * FROM produtos WHERE {' AND '.join(conditions)}"
    rows = get_db().execute(query, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def create(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def update(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome=?, descricao=?, preco=?, estoque=?, categoria=? WHERE id=?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def delete(produto_id):
    db = get_db()
    db.execute("UPDATE produtos SET ativo=0 WHERE id=?", (produto_id,))
    db.commit()
