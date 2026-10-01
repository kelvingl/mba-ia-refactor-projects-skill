from werkzeug.security import generate_password_hash, check_password_hash
from src.models.database import get_db


def _row_to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_all():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_row_to_dict(r) for r in rows]


def get_by_id(usuario_id):
    row = get_db().execute(
        "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def authenticate(email, senha):
    row = get_db().execute(
        "SELECT * FROM usuarios WHERE email = ?", (email,)
    ).fetchone()
    if row and check_password_hash(row["senha_hash"], senha):
        return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
    return None


def create(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, generate_password_hash(senha), tipo),
    )
    db.commit()
    return cursor.lastrowid
