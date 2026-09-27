from .database import get_db
from src.utils.security import hash_password, verify_password

def get_all():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_by_id(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_by_email(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    return dict(row) if row else None

def create(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    password_hash = hash_password(senha)
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, password_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid

def login(email, senha):
    user = get_by_email(email)
    if not user:
        return None
    if not verify_password(senha, user["senha"]):
        return None
    return {
        "id": user["id"],
        "nome": user["nome"],
        "email": user["email"],
        "tipo": user["tipo"]
    }
