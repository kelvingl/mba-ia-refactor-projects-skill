---
Old Project Structure:
task-manager-api/
├── app.py                      # SECRET_KEY hardcoded, debug=True sem condicional
├── database.py                 # db = SQLAlchemy()
├── requirements.txt
├── seed.py
├── models/
│   ├── __init__.py
│   ├── user.py                 # MD5 hash, password exposto em to_dict()
│   ├── task.py                 # is_overdue() e validate_* no model
│   └── category.py
├── routes/
│   ├── __init__.py
│   ├── task_routes.py          # 300 linhas, toda lógica de negócio aqui
│   ├── user_routes.py          # login retorna 'fake-jwt-token-'+id, sem auth guard
│   └── report_routes.py        # categorias e relatórios misturados
├── services/
│   ├── __init__.py
│   └── notification_service.py # credenciais SMTP hardcoded
└── utils/
    ├── __init__.py
    └── helpers.py              # validações duplicadas nunca usadas pelas rotas

---
New Project Structure:
task-manager-api/
├── app.py                          # Composition root (<40 linhas)
├── .env.example                    # Template de variáveis de ambiente
├── requirements.txt                # + PyJWT==2.8.0
├── seed.py                         # Dados de teste com credenciais documentadas
└── src/
    ├── config/
    │   └── settings.py             # required_env (SECRET_KEY obrigatório no boot)
    ├── models/
    │   ├── database.py             # db = SQLAlchemy()
    │   ├── user.py                 # werkzeug hash, sem password em to_dict()
    │   ├── task.py                 # is_overdue() centralizado, _now_utc() naive
    │   └── category.py
    ├── controllers/
    │   ├── authorization.py        # ensure_self_or_admin, ensure_can_set_fields
    │   ├── user_controller.py      # toda lógica de usuário/login
    │   ├── task_controller.py      # joinedload (N+1 fix)
    │   ├── category_controller.py
    │   └── report_controller.py    # joinedload para user_stats (N+1 fix)
    ├── views/
    │   ├── user_routes.py          # ≤10 linhas por rota
    │   ├── task_routes.py
    │   ├── category_routes.py
    │   └── report_routes.py
    ├── middlewares/
    │   ├── error_handler.py        # AppError + handler central via @app.errorhandler
    │   └── auth.py                 # JWT deny-by-default + require_role + PUBLIC_ENDPOINTS
    ├── schemas/
    │   ├── user_schema.py          # Marshmallow — validação centralizada
    │   ├── task_schema.py
    │   └── category_schema.py
    └── utils/
        └── helpers.py              # Helpers puros

---
Output da Fase 1 (Project Analysis)

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1, python-dotenv 1.0.0, requests 2.31.0
Domain:        Task Manager API (tarefas, usuários, categorias, relatórios)
Architecture:  Parcialmente organizada — pastas models/, routes/, services/, utils/ existem mas rotas acumulam validação, lógica de negócio e acesso a banco; sem controllers, sem config separada
Source files:  17 files analyzed
DB tables:     users, tasks, categories
================================

---
Output da Fase 2 (Architecture Audit)

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   17 analyzed | ~600 lines of code

## Summary
CRITICAL: 4 | HIGH: 2 | MEDIUM: 6 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Credentials
**File:** `app.py:13`, `services/notification_service.py:10`
**Description:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` hardcoded no código-fonte. `notification_service.py:10` contém `self.email_password = 'senha123'` — credencial SMTP também hardcoded.
**Impact:** Qualquer pessoa com acesso ao repositório pode forjar tokens. Segredo versionado não pode ser rotacionado sem reescrita de histórico.
**Recommendation:** Mover para variáveis de ambiente lidas em `src/config/settings.py`.

### [CRITICAL] Weak Password Hash + Password Exposed in Response
**File:** `models/user.py:29`, `models/user.py:16-25`
**Description:** Senhas armazenadas com MD5 sem salt. `to_dict()` inclui o campo `password` na resposta.
**Impact:** MD5 quebrado em segundos com rainbow tables; hash exposto via API permite ataques offline.
**Recommendation:** `werkzeug.security.generate_password_hash`; remover `password` do `to_dict()`.

### [CRITICAL] Debug Mode Always On
**File:** `app.py:34`
**Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` sempre ativo.
**Impact:** Werkzeug debugger expõe console Python interativo no servidor.
**Recommendation:** Controlar via `FLASK_DEBUG` env var.

### [CRITICAL] Autenticação Ausente / Token Fake
**File:** `routes/user_routes.py:210`, `routes/user_routes.py:42-90`, `routes/user_routes.py:119-121`
**Description:** Login retorna `'fake-jwt-token-' + str(user.id)`. Nenhum middleware verifica tokens. `POST /users` aceita `role='admin'` sem auth; `PUT /users/<id>` aceita `role` do payload.
**Impact:** Anônimo cria admin; qualquer autenticado se promove a admin via `PUT /users/<id>`.
**Recommendation:** PyJWT + guard global deny-by-default + require_role + ensure_self_or_admin.

### [HIGH] Lógica de Negócio Dentro de Rotas
**File:** `routes/task_routes.py:12-63`, `routes/report_routes.py:13-101`, `routes/user_routes.py:185-211`
**Description:** Funções de rota com 50-90 linhas acumulando parsing, validação, DB e cálculos.
**Impact:** Lógica não testável em isolamento; duplicação inevitável.
**Recommendation:** Extrair para `src/controllers/`.

### [HIGH] Ausência de Tratamento de Erro Centralizado
**File:** `routes/task_routes.py:62`, `routes/user_routes.py:87-90`
**Description:** `except:` nus em cada handler sem tipo e sem log.
**Impact:** Bugs silenciosos; formato de erro inconsistente.
**Recommendation:** `@app.errorhandler` central com exceções tipadas.

### [MEDIUM] N+1 Query em GET /tasks
**File:** `routes/task_routes.py:41-57`
**Description:** Para cada task: `User.query.get()` + `Category.query.get()` — 1+2N queries.
**Recommendation:** `joinedload(Task.user, Task.category)`.

### [MEDIUM] N+1 Query em summary_report
**File:** `routes/report_routes.py:53-68`
**Description:** Para cada usuário: `Task.query.filter_by(user_id=u.id).all()`.
**Recommendation:** `joinedload(User.tasks)`.

### [MEDIUM] Paginação Ausente
**File:** `routes/task_routes.py:14`, `routes/user_routes.py:10-11`
**Description:** `.all()` sem limit/offset.
**Recommendation:** `.paginate()` com `?page=&per_page=`.

### [MEDIUM] Duplicação de Lógica de Validação
**File:** `routes/task_routes.py:110`, `routes/task_routes.py:177`, `routes/user_routes.py:61`, `utils/helpers.py:19-23`
**Description:** Status, email regex e overdue duplicados em 3-4 lugares.
**Recommendation:** Schemas Marshmallow + método único.

### [MEDIUM] Bare `except` Engolindo Erros
**File:** `routes/task_routes.py:62`, `routes/user_routes.py:131`
**Description:** `except:` sem tipo e sem log do erro real.
**Recommendation:** `except Exception as e:` + `logger.exception`.

### [MEDIUM] datetime.utcnow() Deprecated (OBS-01 / OBS-02)
**File:** `models/user.py:14`, `models/task.py:15-16`, `models/category.py:10`
**Description:** `default=datetime.utcnow` deprecated desde Python 3.12.
**Recommendation:** `default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)`.

### [LOW] Log via print
**File:** `routes/task_routes.py:149`, `routes/user_routes.py:83`
**Description:** `print()` sem nível nem formato estruturado.
**Recommendation:** `logging.getLogger(__name__)`.

### [LOW] Checagem de Tipo com `type()` em vez de `isinstance`
**File:** `routes/task_routes.py:141`, `utils/helpers.py:103`
**Description:** `if type(tags) == list:`.
**Recommendation:** `isinstance(tags, list)`.

### [LOW] request.get_json() sem silent=True (OBS-04)
**File:** `routes/task_routes.py:88`, `routes/user_routes.py:44`
**Description:** Sem `silent=True`, levanta exceção com Content-Type inválido.
**Recommendation:** `request.get_json(silent=True)`.

================================
Total: 15 findings
================================

---
Output da Fase 3 (Refactoring to MVC)

================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
task-manager-api/
├── app.py                          # Composition root (<40 linhas)
├── .env.example
├── requirements.txt                # + PyJWT==2.8.0
├── seed.py
└── src/
    ├── config/settings.py          # required_env — SECRET_KEY obrigatório no boot
    ├── models/
    │   ├── database.py
    │   ├── user.py                 # werkzeug hash, sem password em to_dict()
    │   ├── task.py                 # is_overdue() centralizado
    │   └── category.py
    ├── controllers/
    │   ├── authorization.py        # ensure_self_or_admin, ensure_can_set_fields
    │   ├── user_controller.py
    │   ├── task_controller.py      # joinedload (N+1 fix)
    │   ├── category_controller.py
    │   └── report_controller.py    # joinedload (N+1 fix)
    ├── views/
    │   ├── user_routes.py
    │   ├── task_routes.py
    │   ├── category_routes.py
    │   └── report_routes.py
    ├── middlewares/
    │   ├── error_handler.py        # handler central
    │   └── auth.py                 # JWT deny-by-default
    ├── schemas/
    │   ├── user_schema.py
    │   ├── task_schema.py
    │   └── category_schema.py
    └── utils/helpers.py

Validation
  ✓ Application boots without errors
  ✓ GET / responds correctly (200)
  ✓ GET /health responds correctly (200)
  ✓ GET /tasks responds correctly (200 with valid token)
  ✓ POST /tasks responds correctly (201)
  ✓ GET /tasks/stats responds correctly (200)
  ✓ GET /categories responds correctly (200)
  ✓ GET /users responds correctly (200)
  ✓ GET /reports/summary responds correctly (200)

Access control
  Public routes:    GET /, GET /health, POST /login
  Protected routes: all others (401/403 sem credencial — único desvio de contrato)
  ✓ Boot without SECRET_KEY fails with clear error (RuntimeError: "SECRET_KEY não definida", exit=1)
  ✓ GET /tasks without credential → 401
  ✓ GET /tasks with invalid credential → 401
  ✓ GET /tasks with valid credential → 200
  ✓ POST /users with non-admin credential → 403
  ✓ Non-admin setting own role via PUT /users/2 → 403 (role unchanged: "user")
  ✓ Non-admin accessing GET /users/1 (another user's profile) → 403
  ✓ Non-admin accessing GET /users/1/tasks (another user) → 403
  ✓ Non-admin accessing GET /reports/user/1 (another user) → 403
  ✓ Owner id in payload ignored: user_id always comes from token in controller
================================
