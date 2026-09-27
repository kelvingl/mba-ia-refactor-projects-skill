# ecommerce-api-legacy — Estrutura de arquivos: antes × depois

## Antes (legado)

```
./
├── package.json
├── api.http
├── README.md
└── src/
    ├── app.js           # Entry point + criação do Express + bootstrap do AppManager
    ├── AppManager.js    # GOD CLASS: init do banco, todas as rotas, checkout, relatório
    └── utils.js         # Config com secrets hardcoded + globalCache + badCrypto
```

**3 arquivos-fonte · ~181 linhas · 0 camadas separadas**

Problemas estruturais principais:
- `AppManager.js` concentrava DB init, roteamento, lógica de pagamento e relatório financeiro numa única classe
- `utils.js` exportava credenciais de produção em texto claro (`pk_live_`, `senha_super_secreta_prod_123`)
- Callback hell de 4 níveis no checkout e contadores manuais no relatório
- Sem tratamento de erro centralizado, sem autenticação, sem hash de senha real

---

## Depois (MVC)

```
./
├── package.json         # + bcryptjs adicionado
├── .env.example         # Chaves esperadas (PORT, PAYMENT_GATEWAY_KEY, ADMIN_TOKEN)
├── api.http
├── README.md
└── src/
    ├── app.js                          # Composition root (14 linhas)
    │
    ├── config/
    │   └── index.js                    # Lê process.env, expõe config imutável
    │
    ├── models/
    │   ├── db.js                       # DB factory promisificado + initDb()
    │   ├── course.model.js             # findActiveById()
    │   ├── enrollment.model.js         # createEnrollment/Payment/logAudit/getFinancialReport()
    │   └── user.model.js               # findByEmail / create / deleteById()
    │
    ├── controllers/
    │   ├── checkout.controller.js      # Orquestra fluxo de checkout (async/await)
    │   ├── report.controller.js        # Delega para enrollment model
    │   └── user.controller.js          # Delega deleção em cascata para user model
    │
    ├── routes/
    │   ├── index.js                    # Monta todos os routers sob /api
    │   ├── checkout.routes.js          # POST /api/checkout
    │   ├── report.routes.js            # GET  /api/admin/financial-report
    │   └── user.routes.js              # DELETE /api/users/:id
    │
    ├── middlewares/
    │   ├── asyncHandler.js             # Wrapper fn → Promise.catch(next)
    │   ├── errorHandler.js             # Handler central Express (err, req, res, next)
    │   └── requireAdmin.js             # Auth por ADMIN_TOKEN (soft: sem env = aberto)
    │
    └── utils/
        ├── crypto.js                   # hashPassword() via bcryptjs (substituiu badCrypto)
        └── logger.js                   # Logger estruturado com níveis info/warn/error
```

**23 arquivos-fonte · camadas separadas por responsabilidade**

---

## Resumo das transformações

| Anti-pattern (auditoria) | Antes | Depois |
|---|---|---|
| Hardcoded credentials | `utils.js:1-6` — `pk_live_`, `senha_super_secreta_prod_123` no código | `config/index.js` lê `process.env`; `.env.example` documenta as chaves |
| Hash artesanal / plaintext | `badCrypto` (base64 truncado) + seed `'123'` em plaintext | `bcryptjs.hash(pwd, 10)` em `utils/crypto.js` |
| God Class | `AppManager.js` — 8+ responsabilidades, 141 linhas | Distribuído em 4 camadas (models / controllers / routes / middlewares) |
| Callback hell | 4 níveis aninhados + contadores manuais `pending--` | `async/await` com `db.js` promisificado |
| Query N+1 | 1 query/curso × N queries/enrollment × M queries/user+payment | 1 JOIN único em `enrollment.model.js:getFinancialReport()` |
| Integridade referencial | `DELETE users` deixava orphans em enrollments/payments | `deleteById()` remove payments → enrollments → users em ordem |
| Sem error handler | `res.send("Erro")` espalhado em cada callback | `errorHandler.js` central + `asyncHandler` captura erros async |
| Serialização inconsistente | DELETE retornava texto plano; checkout retornava JSON | Todos os endpoints retornam JSON |
| Auth ausente em admin | `/admin/financial-report` e `DELETE /users/:id` sem proteção | Middleware `requireAdmin` aplicado (ativado por `ADMIN_TOKEN` env var) |
| Log de dados sensíveis | `console.log` logava número de cartão e chave do gateway | `logger.js` com níveis; dados de cartão nunca logados |
