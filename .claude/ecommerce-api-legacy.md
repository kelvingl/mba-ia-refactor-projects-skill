# Projeto 2 — ecommerce-api-legacy (Node.js/Express)

LMS API com fluxo de checkout (cursos, matrículas, pagamentos). Monólito com uma
**God Class** central (`AppManager`) que concentra DB, rotas e regra de negócio.

## Como rodar

```bash
cd ecommerce-api-legacy
npm install
npm start
```

Sobe em `http://localhost:3000`. SQLite em memória, com seed automático no boot.
Exemplos de requisição em `api.http`.

## Estrutura atual

```
ecommerce-api-legacy/
├── src/
│   ├── app.js         # bootstrap: cria Express + AppManager
│   ├── AppManager.js  # God Class: schema, seed e TODAS as rotas (checkout, relatório, delete)
│   └── utils.js       # config hardcoded + "crypto" caseiro + cache global
└── api.http
```

Tabelas: `users`, `courses`, `enrollments`, `payments`, `audit_logs`.

## Problemas identificados (análise manual)

- **[CRITICAL] God Class** — [`AppManager.js`](../ecommerce-api-legacy/src/AppManager.js)
  inteiro: uma única classe define schema do banco, seed, e as 3 rotas da aplicação
  (`initDb`, `setupRoutes`), sem nenhuma separação model/controller/route.
- **[CRITICAL] Credenciais e chaves hardcoded** —
  [`utils.js:1-7`](../ecommerce-api-legacy/src/utils.js#L1): `dbPass`,
  `paymentGatewayKey` (`pk_live_...`) e `smtpUser` fixos no código-fonte, e ainda
  logados em texto plano em
  [`AppManager.js:45`](../ecommerce-api-legacy/src/AppManager.js#L45)
  (`console.log` imprime o número do cartão `cc` e a chave do gateway).
- **[CRITICAL] Criptografia de senha quebrada/insegura** —
  [`utils.js:17-23`](../ecommerce-api-legacy/src/utils.js#L17) (`badCrypto`): não é
  hash de verdade, é só Base64 truncado repetido — trivialmente reversível.
- **[HIGH] Lógica de negócio pesada dentro da rota (fat controller)** —
  [`AppManager.js:28-78`](../ecommerce-api-legacy/src/AppManager.js#L28)
  (`POST /api/checkout`): validação, criação de usuário, verificação de pagamento
  (`cc.startsWith("4")` como "gateway" fake) e persistência, tudo em um handler só,
  com callbacks aninhados (callback hell).
- **[HIGH] Estado global mutável** —
  [`utils.js:9-10`](../ecommerce-api-legacy/src/utils.js#L9): `globalCache` e
  `totalRevenue` como variáveis de módulo compartilhadas, sem controle de concorrência.
- **[MEDIUM] N+1 queries** —
  [`AppManager.js:80-129`](../ecommerce-api-legacy/src/AppManager.js#L80)
  (`GET /api/admin/financial-report`): para cada curso, busca matrículas; para cada
  matrícula, busca usuário e pagamento em queries separadas dentro de loops
  aninhados, em vez de JOIN.
- **[MEDIUM] Falta de integridade referencial / soft delete** —
  [`AppManager.js:131-137`](../ecommerce-api-legacy/src/AppManager.js#L131)
  (`DELETE /api/users/:id`): deleta o usuário e a própria resposta admite
  "matrículas e pagamentos ficaram sujos no banco".
- **[LOW] `let self = this` para contornar `this` em callback** —
  [`AppManager.js:26`](../ecommerce-api-legacy/src/AppManager.js#L26) — indício de
  design que não usa arrow functions/async-await de forma consistente.
- **[LOW] Nomes de variável pouco descritivos** —
  [`AppManager.js:29-33`](../ecommerce-api-legacy/src/AppManager.js#L29): `u`, `e`,
  `p`, `cid`, `cc` para dados de entrada do checkout.
- **[LOW] Ausência de tratamento de erro padronizado** — respostas de erro variam
  entre `res.status(...).send("string")` e `res.json({...})` no mesmo arquivo.

## Notas para a skill

- Skill é **copiada** de `code-smells-project/.claude/skills/refactor-arch/` para cá —
  não recriar do zero.
- Bom caso de teste para callback hell / promisificação, além de God Class e segredos
  hardcoded (mesmos padrões do projeto 1, mas em JS/Express).
- Refatoração alvo: `src/models/` (User, Course, Enrollment, Payment), `src/routes/`,
  `src/controllers/` (checkout, financialReport, users), `src/config/` (env vars via
  `.env`, nunca hardcoded), tratamento de erro central (middleware Express).
- Ao validar a Fase 3, checar que `POST /api/checkout` e
  `GET /api/admin/financial-report` (exemplos em `api.http`) continuam funcionando.
