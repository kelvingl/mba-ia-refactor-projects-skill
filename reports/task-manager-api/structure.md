# task-manager-api — Estrutura de Arquivos: Antes × Depois

## Antes da refatoração

```
task-manager-api/
├── app.py                        # Entry point + SECRET_KEY hardcoded + debug=True incondicional
├── database.py                   # db = SQLAlchemy() (arquivo isolado na raiz)
├── requirements.txt
├── seed.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── category.py               # Model OK; default=datetime.utcnow (deprecated)
│   ├── task.py                   # is_overdue() definido mas nunca chamado pelas rotas
│   └── user.py                   # Senha com MD5; hash exposto em to_dict()
├── routes/                       # Roteamento + validação + lógica de negócio misturados
│   ├── __init__.py
│   ├── report_routes.py          # 224 linhas: relatórios E CRUD de categorias no mesmo arquivo
│   ├── task_routes.py            # 300 linhas: N+1 queries + lógica de overdue duplicada
│   └── user_routes.py            # Login retorna 'fake-jwt-token-<id>'; sem guard de auth
├── services/
│   ├── __init__.py
│   └── notification_service.py   # Credenciais SMTP hardcoded; nunca chamado por nenhuma rota
└── utils/
    ├── __init__.py
    └── helpers.py                # Validações duplicadas + print() + type() vs isinstance()
```

**Problemas estruturais:**
- `SECRET_KEY = 'super-secret-key-123'` hardcoded em `app.py:13`
- Senha armazenada com MD5 sem sal (`models/user.py:28–29`)
- Hash da senha exposto na resposta (`models/user.py:20`)
- `app.run(debug=True)` incondicional (`app.py:34`)
- Token falso previsível no login (`routes/user_routes.py:210`)
- Nenhuma rota protegida por autenticação
- `routes/task_routes.py` com 300 linhas: validação + N+1 queries + cálculos inline
- Lógica de `overdue` duplicada em 6 lugares; `Task.is_overdue()` existia mas era ignorado
- `try/except:` genérico espalhado por 7 handlers sem handler central
- `datetime.utcnow()` deprecated em 8+ locais

---

## Depois da refatoração

```
task-manager-api/
├── app.py                        # Composition root puro (<35 linhas, zero lógica)
├── .env.example                  # Template de variáveis de ambiente (SECRET_KEY obrigatória)
├── requirements.txt              # + PyJWT==2.8.0 adicionado
├── seed.py                       # Atualizado para novos caminhos de import
└── src/
    ├── config/
    │   └── settings.py           # _required("SECRET_KEY") — boot falha sem o valor
    ├── models/
    │   ├── database.py           # db = SQLAlchemy()
    │   ├── user.py               # werkzeug hash; password removido de to_dict()
    │   ├── task.py               # is_overdue() usa now_utc(); chamado pelos controllers
    │   └── category.py           # timestamps com now_utc() (sem utcnow deprecated)
    ├── controllers/              # Orquestração por domínio — lógica isolada e testável
    │   ├── task_controller.py    # list/get/create/update/delete/search/stats; joinedload
    │   ├── user_controller.py    # CRUD + login com JWT real
    │   ├── category_controller.py
    │   └── report_controller.py  # Agregações extraídas da rota
    ├── views/                    # Handlers finos: parse → controller → jsonify (≤10 linhas)
    │   ├── task_routes.py
    │   ├── user_routes.py        # @require_role('admin') em POST/DELETE /users
    │   └── report_routes.py
    ├── middlewares/
    │   ├── error_handler.py      # AppError + subclasses tipadas; handler central único
    │   └── auth.py               # Guard deny-by-default (before_request); JWT HS256;
    │                             # PUBLIC_ENDPOINTS allowlist; require_role()
    ├── schemas/
    │   ├── task_schema.py        # CreateTaskSchema / UpdateTaskSchema (Marshmallow)
    │   ├── user_schema.py        # CreateUserSchema / UpdateUserSchema
    │   └── category_schema.py
    └── utils/
        ├── helpers.py            # now_utc(), calculate_percentage(), format_date()
        └── parsing.py            # parse_body(): carrega schema e converte MarshmallowError
```

**Melhorias aplicadas:**
- `SECRET_KEY` e credenciais SMTP lidos de variáveis de ambiente; boot falha sem `SECRET_KEY`
- Senha com `werkzeug.security.generate_password_hash`; campo removido de `to_dict()`
- JWT real via `PyJWT` (HS256, exp 24h); guard global `before_request` deny-by-default
- `POST /users` e `DELETE /users/<id>` exigem `admin`; demais rotas exigem autenticação
- Handlers gordos desmembrados: schema (validação) + controller (lógica) + view (rota)
- `joinedload(Task.user, Task.category)` elimina N+1 em `GET /tasks`
- `is_overdue()` centralizado no model; todas as chamadas removidas das rotas
- `register_error_handlers()` centraliza tratamento de erro; rotas sem try/except
- `datetime.utcnow()` substituído por `now_utc()` (`datetime.now(timezone.utc).replace(tzinfo=None)`) em todos os arquivos
- `notification_service.py` (código morto com credenciais hardcoded) removido

---

## Resumo numérico

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos Python relevantes | 13 | 22 |
| Linhas em `task_routes.py` | 300 | 40 (view fina) |
| Camadas explícitas | 2 (models + routes) | 6 (config, models, controllers, views, middlewares, schemas) |
| Handler central de erros | 0 | 1 (`middlewares/error_handler.py`) |
| Schemas de validação | 0 | 3 domínios × 2 schemas = 6 |
| Queries por `GET /tasks` | 2N+1 | 1 (joinedload) |
| Segredos hardcoded | 3 | 0 |
| Rotas protegidas por auth | 0 | todas exceto `/`, `/health`, `/login` |
| Ocorrências de `utcnow()` deprecated | 8+ | 0 |
