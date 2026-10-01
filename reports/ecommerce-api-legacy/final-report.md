---
Old Project Structure:
src/
├── app.js          (entry point — instancia AppManager e chama setupRoutes)
├── AppManager.js   (God Class — DB init + todas as rotas + lógica + relatório)
└── utils.js        (config com secrets hardcoded + globalCache + badCrypto)

---
New Project Structure:
src/
├── app.js                          (composition root — 20 linhas)
├── config/
│   └── index.js                    (env vars + requiredEnv fail-fast)
├── controllers/
│   ├── checkout.controller.js
│   ├── report.controller.js
│   └── user.controller.js
├── middlewares/
│   ├── auth.js                     (requireAdmin — timingSafeEqual)
│   └── errorHandler.js             (handler central Express)
├── models/
│   ├── db.js                       (promisified sqlite3 + initDb + seed)
│   ├── course.model.js
│   ├── enrollment.model.js
│   ├── payment.model.js
│   └── user.model.js
├── routes/
│   ├── index.js                    (mount order = política de acesso)
│   ├── checkout.routes.js
│   ├── report.routes.js
│   └── user.routes.js
└── utils/
    ├── crypto.js                   (bcryptjs — salt=12)
    ├── errors.js                   (AppError, NotFoundError, etc.)
    └── logger.js                   (logger estruturado JSON)

---
Output da Fase 1 (Project Analysis)

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Node.js
Framework:     Express ^4.18.2
Dependencies:  sqlite3 ^5.1.6
Domain:        LMS/E-commerce API (cursos, matrículas, pagamentos, usuários)
Architecture:  God Class — AppManager centraliza DB, lógica de negócio e rotas em uma única classe (139 linhas)
Source files:  3 files analyzed (app.js, AppManager.js, utils.js)
DB tables:     users, courses, enrollments, payments, audit_logs
================================

---
Output da Fase 2 (Architecture Audit)

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express ^4.18.2
Files:   3 analyzed | ~155 lines of code

## Summary
CRITICAL: 3 | HIGH: 6 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Credentials
**File:** `src/utils.js:2-5`
**Description:** O objeto `config` armazena literalmente no código: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` (chave de produção com prefixo `pk_live_`) e `smtpUser`.
**Impact:** A chave de gateway de pagamento em produção fica exposta no histórico Git para sempre; comprometimento financeiro imediato se vazar.
**Recommendation:** Mover todos os campos para variáveis de ambiente lidas por `src/config/index.js`, com falha de boot se obrigatória não estiver definida.

### [CRITICAL] Weak Hash / Plain Text Password
**File:** `src/utils.js:17-23`, `src/AppManager.js:18`, `src/AppManager.js:68`
**Description:** `badCrypto()` é um loop de base64 que retorna 10 caracteres — não é hash criptográfico. Senha do seed é `'123'` (plain text) e o default é `'123456'` hardcoded.
**Impact:** Qualquer vazamento do banco expõe todas as senhas instantaneamente.
**Recommendation:** Substituir por `bcrypt.hash()` com salt factor >= 12.

### [CRITICAL] God Class / God Module
**File:** `src/AppManager.js:4-141`
**Description:** A classe `AppManager` concentra DB init, todas as rotas, lógica de pagamento, criação de usuário, matrícula, relatório financeiro e audit logging — 8+ responsabilidades em 139 linhas.
**Impact:** Impossível testar qualquer parte em isolamento; qualquer mudança arrasta risco de regressão.
**Recommendation:** Separar em models/, controllers/, routes/, config/ e middlewares/.

### [HIGH] Authentication Absent
**File:** `src/AppManager.js:80-129`, `src/AppManager.js:131-137`
**Description:** Nenhuma rota possui verificação de identidade ou papel. `/api/admin/financial-report` e `DELETE /api/users/:id` estão completamente abertas.
**Impact:** Qualquer usuário anônimo pode acessar dados financeiros ou apagar usuários.
**Recommendation:** Guard de autenticação global com allowlist explícita de rotas públicas (T-15).

### [HIGH] Business Logic Inside Route Handler
**File:** `src/AppManager.js:28-78`
**Description:** Handler `POST /api/checkout` tem 50 linhas com validação, busca/criação de usuário, processamento de pagamento, matrícula e audit log inline.
**Impact:** Lógica impossível de reutilizar ou testar isoladamente.
**Recommendation:** Extrair para CheckoutController + modelos separados.

### [HIGH] Global Mutable State
**File:** `src/utils.js:9-10`
**Description:** `let globalCache = {}` e `let totalRevenue = 0` — cache cresce sem TTL, totalRevenue é dead code.
**Impact:** Memory leak; condição de corrida em requisições concorrentes.
**Recommendation:** Eliminar totalRevenue; encapsular cache com TTL.

### [HIGH] No Centralized Error Handling
**File:** `src/AppManager.js:41,48,51,54,57,60,70`
**Description:** Cada callback trata erros de forma diferente, sem middleware central Express.
**Impact:** Formato de erro inconsistente; stack traces podem vazar ao cliente.
**Recommendation:** Middleware de erro Express (`app.use((err, req, res, next) => {...})`).

### [HIGH] Broken Referential Integrity
**File:** `src/AppManager.js:131-136`
**Description:** `DELETE /api/users/:id` não remove linhas dependentes em enrollments/payments. A mensagem de resposta admite: "matrículas e pagamentos ficaram sujos no banco."
**Impact:** Linhas órfãs corrompem relatórios e causam erros em JOINs futuros.
**Recommendation:** ON DELETE CASCADE no schema + deleção orquestrada no service.

### [HIGH] Callback Hell
**File:** `src/AppManager.js:37-128`
**Description:** Checkout aninha callbacks em 5 níveis. Relatório usa contadores manuais (`coursesPending--`) em vez de Promise.all.
**Impact:** Ordem de execução frágil; erros silenciosos; condição de corrida.
**Recommendation:** Promisificar sqlite3 e reescrever com async/await + Promise.all.

### [MEDIUM] Missing Input Validation
**File:** `src/AppManager.js:35`
**Description:** Checkout valida apenas presença de campos, sem tipo, formato ou range.
**Impact:** Payloads malformados causam exceções não tratadas.
**Recommendation:** Schema de validação por rota (Joi ou Zod).

### [MEDIUM] Inconsistent Serialization / DTO
**File:** `src/AppManager.js:135`
**Description:** `DELETE /api/users/:id` responde plain text; outros endpoints retornam JSON.
**Impact:** Contrato de resposta inconsistente.
**Recommendation:** Padronizar todas as respostas em JSON `{ "message": "..." }`.

### [MEDIUM] N+1 Query
**File:** `src/AppManager.js:83-128`
**Description:** Relatório faz 1 + N + 2*M queries (N=cursos, M=matrículas).
**Impact:** Latência cresce linearmente com volume.
**Recommendation:** JOIN por curso: `SELECT ... FROM enrollments e LEFT JOIN users LEFT JOIN payments`.

### [MEDIUM] Missing Pagination
**File:** `src/AppManager.js:83`
**Description:** `SELECT * FROM courses` sem LIMIT/OFFSET.
**Impact:** Resposta gigante com catálogo grande.
**Recommendation:** Parâmetros `?page=1&limit=20`.

### [LOW] Poor Variable Naming
**File:** `src/AppManager.js:29-34`
**Description:** Variáveis de 1-2 chars em escopo de 50 linhas: `u`, `e`, `p`, `cid`, `cc`.
**Recommendation:** Renomear para `userName`, `email`, `password`, `courseId`, `cardNumber`.

### [LOW] Logging via console.log with Sensitive Data
**File:** `src/AppManager.js:45`, `src/utils.js:13`
**Description:** Loga número de cartão e chave de gateway no stdout sem nível/formato.
**Impact:** Violação de PCI-DSS.
**Recommendation:** Logger estruturado; nunca logar dados de cartão.

### [LOW] sqlite3 Callback API (OBS-03)
**File:** `src/AppManager.js:1`
**Description:** `require('sqlite3').verbose()` usa API de callback de 2013 — raiz do callback hell.
**Recommendation:** Promisificar o driver ou migrar para better-sqlite3/sqlite.

================================
Total: 16 findings
================================

---
Output da Fase 3 (Refactoring to MVC)

================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
src/
├── app.js                          (composition root — 20 linhas)
├── config/
│   └── index.js                    (env vars + requiredEnv fail-fast)
├── controllers/
│   ├── checkout.controller.js
│   ├── report.controller.js
│   └── user.controller.js
├── middlewares/
│   ├── auth.js                     (requireAdmin — timingSafeEqual)
│   └── errorHandler.js             (handler central Express)
├── models/
│   ├── db.js                       (promisified sqlite3 + initDb + seed)
│   ├── course.model.js
│   ├── enrollment.model.js
│   ├── payment.model.js
│   └── user.model.js
├── routes/
│   ├── index.js                    (mount order = política de acesso)
│   ├── checkout.routes.js
│   ├── report.routes.js
│   └── user.routes.js
└── utils/
    ├── crypto.js                   (bcryptjs — salt=12)
    ├── errors.js                   (AppError, NotFoundError, etc.)
    └── logger.js                   (logger estruturado JSON)

Validation
  ✓ Application boots without errors
  ✓ POST /api/checkout responds correctly ({"msg":"Sucesso","enrollment_id":N})
  ✓ POST /api/checkout with non-Visa card → 400 Pagamento recusado
  ✓ GET /api/admin/financial-report responds correctly (JSON cursos/revenue/students)
  ✓ DELETE /api/users/:id responds correctly ({"message":"Usuário deletado com sucesso"})
  ✓ DELETE /api/users/:id inexistente → 404 {"error":"Usuário não encontrado"}

Access control
  Public routes:    POST /api/checkout
  Protected routes: GET /api/admin/financial-report, DELETE /api/users/:id (401/403 sem credencial)
  ✓ Boot without ADMIN_TOKEN fails with clear error (exit=1 — "ADMIN_TOKEN não definida...")
  ✓ /api/admin/financial-report without credential → 401
  ✓ /api/admin/financial-report with invalid credential → 401
  ✓ /api/admin/financial-report with valid credential → 200
  ✓ DELETE /api/users/:id without credential → 401
  n/a Non-admin setting own role (API sem usuários autenticados — única credencial é admin token)
  n/a Non-admin accessing another user's resource (idem)
  n/a Owner id in payload ignored (idem)
================================
