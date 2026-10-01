import sqlite3
from flask import g, current_app
from werkzeug.security import generate_password_hash


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE_PATH"],
            check_same_thread=False,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _create_schema(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT DEFAULT '',
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL DEFAULT 0,
            categoria TEXT DEFAULT 'geral',
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            status TEXT NOT NULL DEFAULT 'pendente',
            total REAL NOT NULL DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
            produto_id INTEGER REFERENCES produtos(id) ON DELETE SET NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL
        );
    """)
    db.commit()


def _seed(db):
    if db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return
    db.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        [
            ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
            ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
            ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
            ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
            ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
            ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
            ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
            ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
            ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
            ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
        ],
    )
    db.executemany(
        "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
        [
            ("Admin", "admin@loja.com", generate_password_hash("admin123"), "admin"),
            ("João Silva", "joao@email.com", generate_password_hash("123456"), "cliente"),
            ("Maria Santos", "maria@email.com", generate_password_hash("senha123"), "cliente"),
        ],
    )
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        _create_schema(db)
        _seed(db)
