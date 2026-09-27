================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express ^4.18.2
Files:   3 analyzed | ~181 lines of code

## Summary
CRITICAL: 3 | HIGH: 6 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Credentials
**File:** `src/utils.js:1-6`
**Description:** `config` exporta `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` e `smtpUser` diretamente no código. A chave `pk_live_` é uma chave de produção real de gateway de pagamento hardcoded no repositório.
**Impact:** Qualquer pessoa com acesso ao repositório tem acesso imediato às credenciais de produção, incluindo a chave do gateway de pagamento — vetor direto de fraude financeira.
**Recommendation:** Mover todos os campos de `config` para variáveis de ambiente lidas em `src/config/env.js` com `process.env.PAYMENT_GATEWAY_KEY`, etc.

### [CRITICAL] Senha em texto plano / hash artesanal
**File:** `src/utils.js:17-23`, `src/AppManager.js:18`, `src/AppManager.js:68`
**Description:** A função `badCrypto` faz base64 em loop de 10.000 iterações e trunca em 10 chars — não é uma função de hash segura. O seed inicial insere o usuário Leonan com senha `'123'` em texto plano (linha 18). Novos usuários criados no checkout usam `badCrypto(p || "123456")` (linha 68).
**Impact:** Qualquer vazamento do banco expõe todas as senhas — o "hash" é reversível trivialmente (base64) e tem espaço de apenas 62^10 combinações.
**Recommendation:** Substituir `badCrypto` por `bcrypt.hash(password, 12)`; atualizar o seed para usar bcrypt; nunca armazenar senha em plaintext.

### [CRITICAL] God Class / God Module
**File:** `src/AppManager.js:4-141`
**Description:** A classe `AppManager` concentra inicialização do banco (linhas 10–23), registro de rotas (linhas 25–138), lógica de checkout com processamento de pagamento (linhas 43–64), criação de usuário (linhas 66–75) e geração de relatório financeiro (linhas 80–129) — mais de 8 responsabilidades em 141 linhas.
**Impact:** Impossível testar qualquer parte em isolamento; qualquer alteração em payment processing arrisca quebrar o relatório financeiro e vice-versa.
**Recommendation:** Separar em camadas: `models/` para acesso a dados, `controllers/` para orquestração, `routes/` para roteamento, `services/` para regras de negócio.

### [HIGH] Autenticação ausente em rotas administrativas
**File:** `src/AppManager.js:80`, `src/AppManager.js:131`
**Description:** `GET /api/admin/financial-report` (linha 80) e `DELETE /api/users/:id` (linha 131) não têm nenhum middleware de autenticação ou verificação de papel/role. Qualquer cliente anônimo pode acessar dados financeiros ou deletar usuários.
**Impact:** Acesso não autorizado a dados financeiros sensíveis e deleção arbitrária de usuários sem nenhuma autenticação.
**Recommendation:** Criar middleware `requireAuth` (JWT) e `requireRole('admin')` e aplicar a essas rotas antes dos handlers.

### [HIGH] Lógica de negócio dentro de rota
**File:** `src/AppManager.js:28-78`
**Description:** O handler de `POST /api/checkout` tem 50 linhas misturando validação de entrada, lookup de curso, criação de usuário, simulação de gateway de pagamento, inserção de matrícula, inserção de pagamento e log de auditoria — tudo dentro do callback da rota.
**Impact:** A lógica de pagamento e matrícula é impossível de reutilizar ou testar sem subir um servidor HTTP completo.
**Recommendation:** Extrair para `CheckoutService.processCheckout(data)` no controller/service, deixando a rota apenas fazer parsing do body e chamar o service.

### [HIGH] Estado global mutável
**File:** `src/utils.js:9-10`
**Description:** `let globalCache = {}` e `let totalRevenue = 0` são variáveis de módulo exportadas e mutadas por múltiplas requisições. `globalCache` cresce indefinidamente sem TTL.
**Impact:** Em ambiente com múltiplas requisições concorrentes, causa condições de corrida e memória crescente sem limite.
**Recommendation:** Encapsular o cache em uma classe com TTL ou usar solução externa (Redis); remover `totalRevenue` global — calculá-lo sob demanda via query.

### [HIGH] Ausência de tratamento de erro centralizado
**File:** `src/AppManager.js:41`, `src/AppManager.js:51`, `src/AppManager.js:55`, `src/AppManager.js:69`
**Description:** Cada callback de erro dentro das rotas chama `res.status(5xx).send("mensagem diferente")` diretamente — sem middleware de erro centralizado no Express, cada ponto de falha formata a resposta de forma ad hoc.
**Impact:** Formato de erro inconsistente entre endpoints; qualquer mudança no padrão de erro exige editar cada `send` individualmente.
**Recommendation:** Adicionar middleware `errorHandler(err, req, res, next)` no Express e usar `next(err)` em vez de `res.send` direto nos callbacks de erro.

### [HIGH] Integridade referencial quebrada
**File:** `src/AppManager.js:131-136`
**Description:** `DELETE /api/users/:id` deleta o usuário sem remover as linhas dependentes em `enrollments` e `payments`. A própria resposta admite: `"as matrículas e pagamentos ficaram sujos no banco"`.
**Impact:** Chaves estrangeiras órfãs em `enrollments.user_id` causam dados corrompidos em qualquer relatório que faça JOIN com `users`.
**Recommendation:** Usar `ON DELETE CASCADE` no schema ou criar um `UserService.deleteUser(id)` que orquestre a deleção na ordem correta (payments → enrollments → users).

### [HIGH] Callback Hell
**File:** `src/AppManager.js:28-128`
**Description:** O handler de checkout tem 4 níveis de callbacks aninhados (linhas 37→40→50→54→57). O relatório financeiro usa contadores manuais `coursesPending--` e `enrPending--` para sincronizar múltiplos callbacks assíncronos em vez de `Promise.all`.
**Impact:** Ordem de execução frágil, erros silenciosamente perdidos nos callbacks internos, condição de corrida nos contadores manuais se o sqlite3 executar callbacks fora de ordem.
**Recommendation:** Promisificar o driver sqlite3 com `util.promisify` ou migrar para `better-sqlite3` (síncrono), reescrever os handlers com `async/await` e `Promise.all` para fan-out.

### [MEDIUM] Validação de entrada ausente na rota
**File:** `src/AppManager.js:29-34`
**Description:** O checkout lê `req.body.usr`, `req.body.eml`, `req.body.c_id` e `req.body.card` sem validar tipos, formato de e-mail ou se `c_id` é numérico. A checagem só verifica presença (linha 35).
**Impact:** Payloads malformados causam comportamento indefinido (ex.: `c_id` como string passando na query parametrizada retorna resultado inesperado).
**Recommendation:** Aplicar schema de validação com Joi ou Zod antes do handler; validar formato de e-mail e que `c_id` é inteiro positivo.

### [MEDIUM] Serialização/DTO inconsistente
**File:** `src/AppManager.js:60`, `src/AppManager.js:135`
**Description:** O checkout retorna `res.status(200).json({ msg: "Sucesso", enrollment_id: enrId })` enquanto o delete de usuário retorna `res.send("Usuário deletado, mas as matrículas...")` como texto plano.
**Impact:** Clientes da API não podem tratar respostas de forma uniforme — cada endpoint tem um contrato diferente.
**Recommendation:** Padronizar todas as respostas em JSON com envelope `{ success, data, message }` via helper centralizado.

### [MEDIUM] Query N+1
**File:** `src/AppManager.js:89-128`
**Description:** O relatório financeiro faz: 1 query de cursos → N queries de enrollments (uma por curso) → N×M queries de users e payments (uma por enrollment). Com 10 cursos e 50 alunos cada, são 1001+ queries por requisição.
**Impact:** Latência cresce quadraticamente com volume de dados; com base de dados real causaria timeouts em produção.
**Recommendation:** Substituir as queries aninhadas por um único JOIN: `SELECT c.title, u.name, p.amount, p.status FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id LEFT JOIN users u ON u.id = e.user_id LEFT JOIN payments p ON p.enrollment_id = e.id`.

### [LOW] Nomenclatura de variável pobre
**File:** `src/AppManager.js:29-33`
**Description:** Variáveis de escopo de 50 linhas nomeadas `u` (username), `e` (email), `p` (password), `cid` (course_id), `cc` (credit card number).
**Recommendation:** Renomear para nomes descritivos: `username`, `email`, `password`, `courseId`, `cardNumber`.

### [LOW] Log via console.log
**File:** `src/AppManager.js:45`, `src/utils.js:13`
**Description:** `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` loga o número do cartão de crédito do cliente e a chave do gateway juntos no stdout. `logAndCache` também usa `console.log` sem nível.
**Recommendation:** Substituir por logger estruturado (pino/winston) com níveis; nunca logar dados de cartão — viola PCI-DSS.

### [LOW] sqlite3 com API de callback obsoleta (OBS-03)
**File:** `src/AppManager.js:1`
**Description:** `require('sqlite3').verbose()` usa a API de callback legada. Em projetos novos Node.js, o padrão é `better-sqlite3` (síncrono) ou `sqlite` (promise-based).
**Recommendation:** Migrar para `better-sqlite3` para eliminar o callback hell e simplificar todas as queries do projeto.

================================
Total: 15 findings
================================
