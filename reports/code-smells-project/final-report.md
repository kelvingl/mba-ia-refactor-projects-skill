---
Old Project Structure:
code-smells-project/
├── app.py           (entry point + 2 admin routes + index route, 89 linhas)
├── controllers.py   (14 funções de rota, 293 linhas)
├── database.py      (conexão global mutável + schema + seed, 87 linhas)
├── models.py        (queries SQL + lógica de negócio + serialização, 315 linhas)
├── requirements.txt
└── README.md

---
New Project Structure:
code-smells-project/
├── app.py               (entry point — 5 linhas)
├── requirements.txt
├── .env.example
├── .gitignore
└── src/
    ├── __init__.py
    ├── app.py           (composition root / factory, 34 linhas)
    ├── config/
    │   ├── __init__.py
    │   └── settings.py  (lê env vars, SECRET_KEY obrigatória)
    ├── models/
    │   ├── __init__.py
    │   ├── database.py      (get_db via flask.g, init_app, schema, seed)
    │   ├── produto_model.py (queries parametrizadas, soft-delete)
    │   ├── usuario_model.py (bcrypt hash/verify, sem retorno de senha)
    │   ├── pedido_model.py  (JOIN único — sem N+1, FK ON DELETE CASCADE)
    │   └── relatorio_model.py
    ├── controllers/
    │   ├── __init__.py
    │   ├── produto_controller.py  (validação centralizada)
    │   ├── usuario_controller.py  (ensure_self_or_admin)
    │   ├── pedido_controller.py   (usuario_id do token, IDOR protegido)
    │   └── relatorio_controller.py
    ├── views/
    │   ├── __init__.py
    │   ├── health_routes.py
    │   ├── produto_routes.py  (GET público, escrita admin-only)
    │   ├── usuario_routes.py
    │   ├── pedido_routes.py
    │   └── relatorio_routes.py
    └── middlewares/
        ├── __init__.py
        ├── error_handler.py  (AppError + subclasses + handler central)
        └── auth.py           (JWT deny-by-default, PUBLIC_ENDPOINTS, require_role)

---
Output da Fase 1 (Project Analysis)
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1, sqlite3 (stdlib)
Domain:        E-commerce API (produtos, pedidos, usuários, relatórios de vendas)
Architecture:  Monolítica por arquivo — 4 arquivos na raiz (app.py, controllers.py,
               database.py, models.py) sem separação de camadas; src/ existia mas vazia
Source files:  4 files analyzed (~784 lines)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================

---
Output da Fase 2 (Architecture Audit)
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~784 lines of code

Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 4 | LOW: 2

Findings

[CRITICAL] SQL Injection — models.py:28,47-50,57-60,65-67,92,109-111,126-129,140,148-165,174,188,192,279-298
[CRITICAL] Hardcoded Credentials — app.py:7, controllers.py:289
[CRITICAL] Plaintext Password Storage — models.py:109-131, database.py:75-83
[CRITICAL] Endpoint de Execução Arbitrária de SQL — app.py:47-78
[CRITICAL] Debug Mode Habilitado em Produção — app.py:8,88, controllers.py:283-290
[HIGH] Authentication Absent — app.py:1-88, controllers.py:128-134,188-220,222-227
[HIGH] God Module — models.py:1-315
[HIGH] Global Mutable State — database.py:4-12
[HIGH] Missing Centralized Error Handling — controllers.py:5-292
[MEDIUM] N+1 Query — models.py:171-233
[MEDIUM] Missing Pagination — models.py:6-22,203-233
[MEDIUM] Duplicated Validation Logic — controllers.py:24-55,64-92
[MEDIUM] Referential Integrity Broken — models.py:65-70, database.py:14-52
[LOW] Log via print — controllers.py:8,106,161,179,208-210,247-250
[LOW] request.get_json() Without silent=True (OBS-04) — controllers.py:26,66,148,169,190,239

Total: 15 findings

---
Output da Fase 3 (Refactoring to MVC)
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
code-smells-project/
├── app.py               (entry point — 5 linhas)
├── requirements.txt
├── .env.example
├── .gitignore
└── src/
    ├── app.py           (composition root)
    ├── config/settings.py
    ├── models/database.py + produto_model.py + usuario_model.py + pedido_model.py + relatorio_model.py
    ├── controllers/produto_controller.py + usuario_controller.py + pedido_controller.py + relatorio_controller.py
    ├── views/health_routes.py + produto_routes.py + usuario_routes.py + pedido_routes.py + relatorio_routes.py
    └── middlewares/error_handler.py + auth.py

Validation
  ✓ Application boots without errors
  ✓ GET /           → 200
  ✓ GET /health     → 200
  ✓ GET /produtos   → 200
  ✓ GET /produtos/1 → 200
  ✓ GET /relatorios/vendas (admin) → 200

Access control
  Public routes:    GET /, GET /health, GET /produtos, GET /produtos/busca, GET /produtos/<id>, POST /login
  Protected routes: todos os outros endpoints (401/403 sem credencial)

  ✓ Boot sem SECRET_KEY falha com RuntimeError e exit=1
  ✓ GET /usuarios sem token → 401
  ✓ GET /usuarios com token inválido → 401
  ✓ GET /usuarios com token admin → 200
  ✓ GET /usuarios (token de usuario comum) → 403
  ✓ POST /usuarios (token de usuario comum) → 403
  ✓ GET /relatorios/vendas (token de usuario comum) → 403
  ✓ GET /usuarios/1 (usuário comum acessando admin) → 403
  ✓ GET /usuarios/2 (usuário comum acessando próprio perfil) → 200
  ✓ POST /pedidos com {"usuario_id":1} no corpo usando token do usuario_id=2 → pedido criado com usuario_id=2 (id do token)
  ✓ GET /pedidos/usuario/2 (proprio usuário) → 200
  ✓ GET /pedidos/usuario/1 (outro usuário, não-admin) → 403
================================
