# task-manager-api — Estrutura de Arquivos: Antes × Depois

## Antes da refatoração

```
.
├── app.py                        # Entry point + config hardcoded + blueprints
├── database.py                   # db = SQLAlchemy() (raiz do projeto)
├── requirements.txt
├── seed.py
├── README.md
├── models/
│   ├── __init__.py               # Importa os 3 models
│   ├── category.py               # Model OK, mas default=datetime.utcnow (deprecated)
│   ├── task.py                   # Lógica de validação no model + utcnow deprecated
│   └── user.py                   # MD5 para senha + password exposto no to_dict()
├── routes/                       # Camada "controller" + roteamento misturados
│   ├── __init__.py
│   ├── report_routes.py          # 224 linhas: relatórios E categorias no mesmo arquivo
│   ├── task_routes.py            # 300 linhas: validação + N+1 queries + lógica de negócio
│   └── user_routes.py            # Login retorna fake-jwt-token-<id>
├── services/
│   ├── __init__.py
│   └── notification_service.py   # SMTP user/password hardcoded no construtor
└── utils/
    ├── __init__.py
    └── helpers.py                # Validação duplicada + print() + type() ao invés de isinstance()
```

**Problemas identificados:**
- `SECRET_KEY = 'super-secret-key-123'` hardcoded em `app.py:13`
- Senha armazenada com MD5 sem sal (`models/user.py:29`)
- Hash da senha exposto na resposta via `to_dict()` (`models/user.py:20`)
- `app.run(debug=True)` sem verificação de ambiente (`app.py:34`)
- Token de autenticação falso (`routes/user_routes.py:210`)
- `task_routes.py` com 300 linhas misturando roteamento, validação e lógica
- N+1 queries em `GET /tasks` (2 queries extras por task) e `GET /reports/summary`
- `try/except:` genérico espalhado por 5+ handlers sem handler central
- `datetime.utcnow()` deprecated em 8+ locais
- Deleção de usuário com loop manual sem cascade no schema

---

## Depois da refatoração

```
.
├── app.py                        # Composition root puro (43 linhas)
├── .env.example                  # Template de variáveis de ambiente
├── requirements.txt              # + PyJWT adicionado
├── seed.py
├── README.md
│
├── config/
│   ├── __init__.py
│   └── settings.py               # Lê SECRET_KEY, FLASK_DEBUG, DATABASE_URL, SMTP_* de env
│
├── models/
│   ├── __init__.py
│   ├── database.py               # db = SQLAlchemy() (movido da raiz)
│   ├── category.py               # timestamps com datetime.now(timezone.utc)
│   ├── task.py                   # Relacionamentos explícitos, is_overdue() limpo
│   └── user.py                   # werkzeug hash, sem password em to_dict(),
│                                 # cascade='all, delete-orphan' em User.tasks
│
├── controllers/
│   ├── __init__.py
│   ├── task_controller.py        # CRUD + stats; joinedload(Task.user, Task.category)
│   ├── user_controller.py        # CRUD + JWT real (PyJWT); subqueryload(User.tasks)
│   └── report_controller.py      # Relatórios + CRUD de categorias
│
├── views/                        # Blueprints finos (~5 linhas por handler)
│   ├── __init__.py
│   ├── task_routes.py            # Schema.load() → controller → jsonify()
│   ├── user_routes.py
│   └── report_routes.py
│
├── middlewares/
│   ├── __init__.py
│   └── error_handler.py          # AppError, NotFoundError, BadRequestError, ...
│                                 # register_error_handlers() — handler central único
│
├── schemas/
│   ├── __init__.py
│   ├── task_schema.py            # CreateTaskSchema, UpdateTaskSchema (Marshmallow)
│   └── user_schema.py            # CreateUserSchema, UpdateUserSchema
│
├── services/
│   ├── __init__.py
│   └── notification_service.py   # SMTP lido de settings (sem credencial no código)
│
└── utils/
    ├── __init__.py
    └── helpers.py                # Funções puras: now_utc(), parse_date(), validate_email()
```

**Melhorias aplicadas:**
- `SECRET_KEY` e credenciais SMTP lidos de variáveis de ambiente via `config/settings.py`
- Senha com `werkzeug.security.generate_password_hash` (bcrypt/pbkdf2); removida do `to_dict()`
- `debug` controlado por `FLASK_DEBUG` env var
- JWT real via `PyJWT` com expiração de 24h
- God module `task_routes.py` desmembrado em schema + controller + view
- `joinedload` e `subqueryload` eliminam queries N+1
- `register_error_handlers()` centraliza todo tratamento de erro; routes sem try/except
- `cascade='all, delete-orphan'` no relacionamento `User.tasks`
- `datetime.utcnow()` substituído por `datetime.now(timezone.utc).replace(tzinfo=None)` em todos os modelos e controllers

---

## Resumo numérico

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos Python relevantes | 13 | 21 |
| Linhas em `task_routes.py` | 300 | ~50 (view fina) |
| Camadas explícitas | 2 (models + routes) | 6 (config, models, controllers, views, middlewares, schemas) |
| Handlers de erro centralizados | 0 | 1 (`error_handler.py`) |
| Schemas de validação | 0 | 4 (Create/Update × Task/User) |
| Queries por `GET /tasks` | 2N+1 | 1 (joinedload) |
| Segredos hardcoded | 3 | 0 |
| API deprecated (`utcnow`) | 8+ ocorrências | 0 |
