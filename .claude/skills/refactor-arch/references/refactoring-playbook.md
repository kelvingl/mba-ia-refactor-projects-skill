# Playbook de Refatoração

Transformações concretas para a **Fase 3**, uma por anti-pattern do catálogo, com
exemplo de **antes/depois**. A ordem aqui já é a ordem sugerida de execução — comece do
topo e desça.

> Regra fixa: o contrato observável (método HTTP + path + shape da resposta) **não
> muda**. Só altere a shape de uma resposta se o contrato de entrada já estiver quebrado
> por outro motivo (ex.: o endpoint `/admin/query`, que será deletado, não refatorado).
> Única exceção de status code: rotas que passam a exigir autenticação (T-15) respondem
> 401/403 a quem não tem credencial — com credencial válida, o contrato original vale.

---

## T-01 — Segredos hardcoded → módulo de config + variáveis de ambiente

### Antes (Python)
```python
# app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

### Depois (Python)
```python
# src/config/settings.py
import os

def required_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} não definida — copie .env.example para .env e preencha")
    return value

class Settings:
    SECRET_KEY = required_env("SECRET_KEY")   # protege acesso → obrigatório, sem default
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///loja.db")

settings = Settings()
```
```python
# src/app.py
from src.config.settings import settings
app.config["SECRET_KEY"] = settings.SECRET_KEY
app.config["DEBUG"] = settings.DEBUG
```

### Antes (Node.js)
```javascript
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_..." };
```

### Depois (Node.js)
```javascript
// src/config/index.js
require('dotenv').config();

function requiredEnv(name) {
  const value = (process.env[name] || '').trim();
  if (!value) throw new Error(`${name} não definida — copie .env.example para .env e preencha`);
  return value;
}

module.exports = {
  port: parseInt(process.env.PORT || '3000', 10),
  adminToken: requiredEnv('ADMIN_TOKEN'),           // protege acesso → obrigatório
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',  // credencial de terceiro
  dbUser: process.env.DB_USER || '',
  dbPass: process.env.DB_PASS || '',
};
```

**Regra para defaults:** valor não sensível (porta, URL de banco local, flag de debug)
pode ter default. Segredo que **protege o acesso a esta aplicação** — chave de
assinatura de sessão/JWT, token de admin/API key que a própria aplicação confere —
**nunca** tem default nem cai em `''`: use `required_env`/`requiredEnv` e deixe a
aplicação falhar no boot (fail-fast). Um default como `"dev-only-change-me"` é público
(está no repositório) e permite forjar tokens; um `''` faz guards do tipo
`if (!token) return next()` liberarem tudo (ver T-15). Credenciais de serviços de
terceiros (gateway, SMTP) podem ficar vazias, desde que o código que as usa trate a
ausência sem quebrar o boot.

**Extra:** crie `.env.example` com as chaves, marcando as obrigatórias com um
comentário (`# obrigatório — a aplicação não sobe sem este valor`), e garanta `.env` no
`.gitignore`. Se o projeto não carregava `.env` antes, adicione o loader
(`python-dotenv`, `dotenv`) para que `cp .env.example .env` baste para rodar.

---

## T-02 — SQL Injection → prepared statements

### Antes (Python/SQLite)
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute(
    "INSERT INTO usuarios (nome, email, senha) VALUES ('" + nome + "', '" + email + "', '" + senha + "')"
)
```

### Depois (Python/SQLite)
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute(
    "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
    (nome, email, senha),
)
```

### Antes (Node.js com template literal)
```javascript
db.all(`SELECT * FROM users WHERE email='${email}'`, callback);
```

### Depois (Node.js)
```javascript
db.all("SELECT * FROM users WHERE email = ?", [email], callback);
```

Para filtros dinâmicos com múltiplas condições opcionais, monte a query com placeholders
e um array de bindings:

```python
conditions, params = ["1=1"], []
if termo:
    conditions.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
if categoria:
    conditions.append("categoria = ?")
    params.append(categoria)
query = f"SELECT * FROM produtos WHERE {' AND '.join(conditions)}"
cursor.execute(query, params)
```

---

## T-03 — Senha fraca (plaintext/MD5) → hash forte + nunca retornar

### Antes (Python)
```python
# models/user.py
self.password = hashlib.md5(pwd.encode()).hexdigest()

def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password, ...}
```

### Depois (Python — werkzeug, sem dependência nova)
```python
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    ...
    def set_password(self, plain):
        self.password_hash = generate_password_hash(plain)

    def check_password(self, plain):
        return check_password_hash(self.password_hash, plain)

    def to_dict(self):
        return {"id": self.id, "email": self.email, "role": self.role}  # sem password
```

### Antes (Node.js — crypto artesanal)
```javascript
function badCrypto(pwd) {
  let hash = "";
  for(let i = 0; i < 10000; i++) hash += Buffer.from(pwd).toString('base64').substring(0, 2);
  return hash.substring(0, 10);
}
```

### Depois (Node.js — bcrypt)
```javascript
const bcrypt = require('bcryptjs');
async function hashPassword(plain) { return bcrypt.hash(plain, 10); }
async function verifyPassword(plain, hash) { return bcrypt.compare(plain, hash); }
```

Adicione `bcrypt`/`bcryptjs` ao `package.json`. Nunca inclua `password`/`password_hash`
em nenhuma resposta.

---

## T-04 — Estado global mutável → factory / escopo por sessão

### Antes (Python)
```python
# database.py
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(...)
    return db_connection
```

### Depois
```python
# src/models/database.py
import sqlite3
from flask import g, current_app

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"], check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
```

### Antes (Node.js)
```javascript
let globalCache = {};
let totalRevenue = 0;
```

### Depois
```javascript
// remova totalRevenue por completo — calcule sob demanda na rota de relatório
// se cache for realmente necessário, use uma lib com TTL (node-cache, lru-cache) encapsulada em um módulo
```

---

## T-05 — God Class → camadas por domínio

### Antes
`models.py` (350 linhas) com queries de produtos, usuários, pedidos, relatórios, cálculo
de desconto e notificações. `AppManager.js` com init do DB, todas as rotas, checkout e
relatório no mesmo arquivo.

### Depois
```
src/
├── models/
│   ├── produto_model.py    # só acesso a "produtos"
│   ├── usuario_model.py
│   ├── pedido_model.py
│   └── database.py
├── controllers/
│   ├── produto_controller.py
│   ├── pedido_controller.py
│   └── relatorio_controller.py
└── views/
    └── routes.py           # Blueprint registrando endpoints
```

**Passo a passo:**
1. Liste cada função do God Class/God Module.
2. Atribua cada função a um domínio (produto, pedido, usuário...).
3. Atribua cada função a uma camada (acesso a dado → model; validação/orquestração → controller; rota → view).
4. Mova uma função por vez preservando a assinatura, atualizando os imports de quem chama.

---

## T-06 — Lógica de negócio na rota → controller dedicado

### Antes (Python/Flask)
```python
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data: return jsonify({'error': 'Dados inválidos'}), 400
    title = data.get('title')
    if not title: return jsonify({'error': 'Título é obrigatório'}), 400
    if len(title) < 3: return jsonify({'error': 'Título muito curto'}), 400
    # ...15 linhas de validação...
    # ...5 linhas de query...
    # ...2 linhas de notificação...
    return jsonify(task.to_dict()), 201
```

### Depois

`src/schemas/task_schema.py` — schema declarativo:
```python
from marshmallow import Schema, fields, validate

class CreateTaskSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(load_default="")
    status = fields.Str(load_default="pending", validate=validate.OneOf(['pending','in_progress','done','cancelled']))
    priority = fields.Int(load_default=3, validate=validate.Range(min=1, max=5))
    user_id = fields.Int(load_default=None)
    category_id = fields.Int(load_default=None)
    due_date = fields.Date(load_default=None)
    tags = fields.List(fields.Str(), load_default=[])
```

`src/controllers/task_controller.py`:
```python
def create_task(payload):
    task = Task(**payload, tags=','.join(payload.get('tags', [])))
    db.session.add(task); db.session.commit()
    return task
```

`src/views/task_routes.py`:
```python
@task_bp.route('/tasks', methods=['POST'])
def create_task_route():
    payload = CreateTaskSchema().load(request.get_json() or {})
    task = task_controller.create_task(payload)
    return jsonify(serialize_task(task)), 201
```

A rota volta a ter 4 linhas. Validação mora no schema, orquestração no controller.

---

## T-07 — `try/except` disperso → error handler central

### Antes (Python/Flask)
```python
def listar_produtos():
    try:
        produtos = models.get_todos_produtos()
        return jsonify(...), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

### Depois

`src/middlewares/error_handler.py`:
```python
class AppError(Exception):
    status_code = 500
    message = "Erro interno"
    def __init__(self, message=None):
        if message: self.message = message

class NotFoundError(AppError):       status_code = 404; message = "Recurso não encontrado"
class ValidationError(AppError):     status_code = 400
class UnauthorizedError(AppError):   status_code = 401

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno"}), 500
```

`src/controllers/produto_controller.py`:
```python
def listar_produtos():
    return produto_model.get_all()
```

`src/views/produto_routes.py`:
```python
@produto_bp.route("/produtos", methods=["GET"])
def listar_produtos_route():
    produtos = produto_controller.listar_produtos()
    return jsonify({"dados": produtos, "sucesso": True}), 200
```

### Equivalente em Express
```javascript
// middlewares/errorHandler.js
function errorHandler(err, req, res, next) {
  const status = err.statusCode || 500;
  if (status >= 500) console.error(err);
  res.status(status).json({ error: err.message || 'Erro interno' });
}
module.exports = errorHandler;

// app.js
app.use(errorHandler);  // sempre por último
```

Use `next(err)` ou `throw` em handlers async com um wrapper:
```javascript
const asyncHandler = fn => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
router.get('/users/:id', asyncHandler(async (req, res) => { ... }));
```

---

## T-08 — Callback hell → `async/await` + `Promise.all`

### Antes (Node.js)
```javascript
this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
  this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
    this.db.run("INSERT INTO enrollments ...", [...], function(err) {
      const enrId = this.lastID;
      self.db.run("INSERT INTO payments ...", [...], function(err) {
        self.db.run("INSERT INTO audit_logs ...", [...], (err) => {
          res.json({enrollment_id: enrId});
        });
      });
    });
  });
});
```

### Depois (Node.js)
```javascript
// src/models/db.js — promisify uma vez
const sqlite3 = require('sqlite3');
const { promisify } = require('util');

function createDb(path = ':memory:') {
  const raw = new sqlite3.Database(path);
  return {
    all:  promisify(raw.all.bind(raw)),
    get:  promisify(raw.get.bind(raw)),
    run:  (sql, params = []) => new Promise((resolve, reject) => {
      raw.run(sql, params, function(err) { err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes }); });
    }),
    close: promisify(raw.close.bind(raw)),
  };
}
module.exports = { createDb };
```

```javascript
// controllers/checkout.controller.js
async function checkout({ name, email, courseId, card }, db) {
  const course = await db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [courseId]);
  if (!course) throw new NotFoundError('Curso não encontrado');

  let user = await db.get("SELECT id FROM users WHERE email = ?", [email]);
  if (!user) {
    const { lastID } = await db.run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [name, email, await hashPassword(DEFAULT_PWD)]);
    user = { id: lastID };
  }

  const status = card.startsWith("4") ? "PAID" : "DENIED";
  if (status === "DENIED") throw new PaymentRefusedError();

  const enr = await db.run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [user.id, courseId]);
  await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enr.lastID, course.price, status]);
  await db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [`Checkout ${courseId} por ${user.id}`]);

  return { enrollment_id: enr.lastID };
}
```

**Para fan-out (relatório):** use `Promise.all`:
```javascript
const courses = await db.all("SELECT * FROM courses");
const report = await Promise.all(courses.map(async c => {
  const enrollments = await db.all("SELECT e.id, e.user_id, u.name, p.amount, p.status FROM enrollments e LEFT JOIN users u ON u.id = e.user_id LEFT JOIN payments p ON p.enrollment_id = e.id WHERE e.course_id = ?", [c.id]);
  const revenue = enrollments.filter(r => r.status === 'PAID').reduce((acc, r) => acc + r.amount, 0);
  return { course: c.title, revenue, students: enrollments.map(r => ({ student: r.name || 'Unknown', paid: r.amount || 0 })) };
}));
return res.json(report);
```

---

## T-09 — N+1 → JOIN / eager loading

### Antes (Python/SQLite cru)
```python
for row in rows:  # rows = pedidos
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    itens = cursor2.fetchall()
    for item in itens:
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

### Depois (1 query)
```python
cursor.execute("""
    SELECT p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
           ip.produto_id, ip.quantidade, ip.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
    ORDER BY p.id
""")
rows = cursor.fetchall()
pedidos = {}
for r in rows:
    pid = r["pedido_id"]
    if pid not in pedidos:
        pedidos[pid] = { "id": pid, "usuario_id": r["usuario_id"], "status": r["status"], "total": r["total"], "criado_em": r["criado_em"], "itens": [] }
    if r["produto_id"] is not None:
        pedidos[pid]["itens"].append({ "produto_id": r["produto_id"], "produto_nome": r["produto_nome"], "quantidade": r["quantidade"], "preco_unitario": r["preco_unitario"] })
return list(pedidos.values())
```

### SQLAlchemy (eager loading)
```python
from sqlalchemy.orm import joinedload
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
```

---

## T-10 — Integridade referencial quebrada → exclusão orquestrada

### Antes (Node.js)
```javascript
app.delete('/api/users/:id', (req, res) => {
  this.db.run("DELETE FROM users WHERE id = ?", [id], () => {
    res.send("Usuário deletado, mas matrículas e pagamentos ficaram sujos");
  });
});
```

### Depois
```javascript
// controllers/user.controller.js
async function deleteUser(id, db) {
  await db.run("DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)", [id]);
  await db.run("DELETE FROM enrollments WHERE user_id = ?", [id]);
  await db.run("DELETE FROM users WHERE id = ?", [id]);
}
```

E adicione `ON DELETE CASCADE` no schema:
```javascript
"CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, ...)"
```

(No SQLite é preciso habilitar com `PRAGMA foreign_keys = ON;`.)

---

## T-11 — API deprecated `datetime.utcnow()` → `datetime.now(timezone.utc)`

### Antes
```python
created_at = db.Column(db.DateTime, default=datetime.utcnow)
# ...
if t.due_date < datetime.utcnow():
```

### Depois
```python
from datetime import datetime, timezone

def _now_utc():
    return datetime.now(timezone.utc)

created_at = db.Column(db.DateTime, default=_now_utc)
# ...
if t.due_date < _now_utc():
```

---

## T-12 — Endpoint de execução arbitrária → remoção

```python
# DELETAR inteiro:
@app.route("/admin/query", methods=["POST"])
def executar_query():
    ...

@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    ...
```

Se algo assim for necessário em desenvolvimento, crie um script CLI separado
(`scripts/reset_db.py`) — nunca exponha como endpoint HTTP.

---

## T-13 — Validação duplicada → schema/constantes centralizadas

### Antes
`['pending', 'in_progress', 'done', 'cancelled']` repetido em 5 lugares diferentes;
regex de e-mail duplicado em 2 lugares.

### Depois
```python
# src/schemas/constants.py
VALID_TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
VALID_ROLES = ('user', 'admin', 'manager')
EMAIL_RE = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
```

E use schemas com `validate.OneOf(VALID_TASK_STATUSES)`.

---

## T-14 — Log via `print`/`console.log` → logger estruturado

### Antes
```python
print("Listando " + str(len(produtos)) + " produtos")
```

### Depois
```python
# src/utils/logger.py
import logging
logger = logging.getLogger("app")

# controllers/produto_controller.py
logger.info("listing %d produtos", len(produtos))
```

E no `app.py`:
```python
logging.basicConfig(level=logging.INFO if settings.DEBUG else logging.WARNING)
```

---

## T-15 — Autenticação ausente ou fraca → deny-by-default

Aplica-se a todo finding AP-06. O objetivo não é "colocar um decorator nas rotas
sensíveis", é **inverter o default**: toda rota nasce protegida e só fica pública quem
estiver numa allowlist explícita. Decorator por rota sozinho é *fail-open* — a rota que
alguém esquecer de decorar fica aberta.

### Regras (todas obrigatórias)

1. **Segredo obrigatório no boot** (T-01): chave de assinatura e token de admin vêm de
   `required_env`/`requiredEnv`. Nenhum guard trata o caso "segredo vazio" — se a
   aplicação está de pé, o segredo existe.
2. **Proteção no nível do app/router**, não por rota: `before_request` (Flask),
   `router.use(guard)` (Express), filtro global (Spring), middleware de grupo
   (Laravel/Gin). Rotas públicas ficam numa allowlist pequena e comentada.
3. **Todo token emitido tem um verificador ativo.** Login que devolve JWT sem nenhum
   middleware que o confira é o mesmo que não ter autenticação.
4. **JWT:** `algorithms` fixo na verificação, `exp` sempre presente, segredo vindo da
   config. Nunca `verify=False` / `options={"verify_signature": False}`.
5. **Segredo estático** (API key, token de admin) comparado em tempo constante:
   `hmac.compare_digest` (Python), `crypto.timingSafeEqual` (Node).
6. **401** quando falta credencial ou ela é inválida; **403** quando a credencial é válida
   mas o papel não basta.
7. **Operações que concedem ou removem privilégio** (criar usuário, alterar `role`,
   deletar usuário) exigem papel `admin`. O primeiro admin vem de seed/script de CLI —
   nunca de um endpoint aberto.
8. **Contrato:** rota que passa a exigir autenticação pode responder 401/403 sem
   credencial — é o **único** desvio permitido da regra de contrato. Liste essas rotas no
   output da Fase 3 e atualize os exemplos de requisição do projeto (`api.http`, README,
   coleção Postman) com o header necessário.

### Antes (Python/Flask)
```python
@user_bp.route('/login', methods=['POST'])
def login():
    ...
    return jsonify({'token': 'fake-jwt-token-' + str(user.id)})   # token forjável

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])         # nenhuma checagem
def delete_user(user_id): ...
```
Também é "antes": login emitindo um JWT real com `jwt.encode(...)` enquanto nenhuma rota
chama `jwt.decode` — o token existe, mas não protege nada.

### Depois (Python/Flask)
```python
# src/middlewares/auth.py
from datetime import datetime, timedelta, timezone
from functools import wraps
import jwt
from flask import g, request
from config.settings import settings
from middlewares.error_handler import UnauthorizedError, ForbiddenError

JWT_ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=24)

# Únicas rotas acessíveis sem token (nome do endpoint Flask). Toda rota nova nasce protegida.
PUBLIC_ENDPOINTS = {"index", "health", "users.login"}


def issue_token(user):
    claims = {"sub": str(user.id), "role": user.role,
              "exp": datetime.now(timezone.utc) + TOKEN_TTL}
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def authenticate_request():
    # endpoint None = rota inexistente → deixa o Flask responder 404
    if request.method == "OPTIONS" or request.endpoint is None or request.endpoint in PUBLIC_ENDPOINTS:
        return
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("Token ausente")
    try:
        claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise UnauthorizedError("Token inválido ou expirado")
    g.current_user = {"id": int(claims["sub"]), "role": claims.get("role")}


def require_role(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if g.current_user["role"] not in roles:
                raise ForbiddenError("Permissão insuficiente")
            return view(*args, **kwargs)
        return wrapper
    return decorator


def init_auth(app):
    app.before_request(authenticate_request)
```
```python
# src/app.py (composition root)
register_error_handlers(app)
init_auth(app)                      # antes dos blueprints: tudo protegido por padrão

# src/views/user_routes.py
@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_role('admin')
def delete_user(user_id): ...
```

### Antes (Node.js/Express — guard fail-open)
```javascript
function requireAdmin(req, res, next) {
  if (!config.adminToken) return next();          // ADMIN_TOKEN vazio → libera tudo
  if (req.headers['x-admin-token'] !== config.adminToken) { /* 401 */ }
  next();
}
```

### Depois (Node.js/Express)
```javascript
// src/middlewares/auth.js
const crypto = require('crypto');
const config = require('../config');   // T-01: o boot já falhou se ADMIN_TOKEN faltar
const { UnauthorizedError } = require('../utils/errors');

function safeEqual(provided, expected) {
  const a = Buffer.from(String(provided));
  const b = Buffer.from(String(expected));
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

function requireAdmin(req, res, next) {
  const provided = req.get('x-admin-token');
  if (!provided || !safeEqual(provided, config.adminToken)) {
    return next(new UnauthorizedError('Unauthorized'));
  }
  next();
}

module.exports = { requireAdmin };
```
```javascript
// src/routes/index.js — a ordem de montagem É a política de acesso
router.use('/api', checkoutRoutes);     // público: allowlist explícita, montada antes do guard
router.use('/api', requireAdmin);       // daqui para baixo, tudo exige credencial
router.use('/api', reportRoutes);
router.use('/api', userRoutes);
```

Com usuários autenticados por JWT em Express, o desenho é o mesmo do Flask:
`router.use(requireAuth)` global depois das rotas públicas + `requireRole('admin')` nas
rotas de privilégio.

---

## Sequência recomendada na Fase 3

1. **Config primeiro** (T-01) — desbloqueia o resto sem quebrar nada; segredos de acesso já ficam obrigatórios.
2. **Segurança crítica** (T-02, T-03) — SQL injection e senha antes de mexer em mais nada.
3. **Estado e estrutura** (T-04, T-05) — remove globals, quebra o God Class em camadas.
4. **Fluxo de request** (T-06) — controllers assumindo a lógica que estava na rota.
5. **Cross-cutting** (T-07, T-15) — error handler central e, sobre ele, a autenticação deny-by-default (T-15 depende das exceções tipadas do T-07).
6. **Assíncrono e performance** (T-08, T-09) — só depois que a estrutura já está estável.
7. **Integridade de dados** (T-10) e **API deprecated** (T-11).
8. **Limpeza** (T-12, T-13, T-14) e remoção final dos arquivos legados.
9. **Valide** — instale dependências, suba a aplicação, faça `curl` nos endpoints originais e rode a matriz de autenticação.

## Validação final (Fase 3)

Exporte valores **de teste** para os segredos obrigatórios antes do boot (ou crie um
`.env` local, que não é commitado). Nunca commite esses valores.

Para Python/Flask:
```bash
pip install -r requirements.txt

# 1) boot sem o segredo precisa falhar com mensagem clara (fail-fast)
env -u SECRET_KEY python app.py; echo "exit=$?"   # esperado: exit != 0 e "SECRET_KEY não definida"

# 2) boot normal
export SECRET_KEY=test-secret-validation
python app.py &
APP_PID=$!
sleep 3
curl -sS http://localhost:5000/ | head                                     # pública → 200
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost:5000/<rota-protegida>        # → 401
curl -sS -o /dev/null -w '%{http_code}\n' -H 'Authorization: Bearer invalido' http://localhost:5000/<rota-protegida>  # → 401
TOKEN=$(curl -sS -X POST http://localhost:5000/login -H 'Content-Type: application/json' \
        -d '{"email":"<admin-do-seed>","password":"<senha>"}' | python -c 'import sys,json; print(json.load(sys.stdin)["token"])')
curl -sS -H "Authorization: Bearer $TOKEN" http://localhost:5000/<rota-protegida> | head  # → 2xx
# token de usuário comum numa rota de admin → 403
kill $APP_PID
```

Para Node.js/Express:
```bash
npm install
env -u ADMIN_TOKEN node src/app.js; echo "exit=$?"        # esperado: exit != 0
export ADMIN_TOKEN=test-admin-token
node src/app.js &
APP_PID=$!
sleep 3
curl -sS http://localhost:3000/<endpoint-publico> | head                                  # → 2xx
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost:3000/<rota-admin>              # → 401
curl -sS -o /dev/null -w '%{http_code}\n' -H 'X-Admin-Token: errado' http://localhost:3000/<rota-admin>  # → 401
curl -sS -H "X-Admin-Token: $ADMIN_TOKEN" http://localhost:3000/<rota-admin> | head      # → 2xx
kill $APP_PID
```

Se qualquer comando retornar 5xx, não conectar, ou uma rota protegida responder 2xx sem
credencial, **corrija antes de declarar sucesso**.
