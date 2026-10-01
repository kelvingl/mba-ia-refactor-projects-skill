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
**Description:** O objeto `config` armazena literalmente no código: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` (chave de produção com prefixo `pk_live_`) e `smtpUser`. Qualquer pessoa com acesso ao repositório tem essas credenciais.
**Impact:** A chave de gateway de pagamento em produção fica exposta no histórico Git para sempre; comprometimento financeiro imediato se vazar.
**Recommendation:** Mover todos os campos para variáveis de ambiente (`PAYMENT_GATEWAY_KEY`, `DB_PASS`, etc.) lidas por um módulo `src/config/index.js`, com falha de boot se obrigatória não estiver definida.

### [CRITICAL] Weak Hash / Plain Text Password
**File:** `src/utils.js:17-23`, `src/AppManager.js:18`, `src/AppManager.js:68`
**Description:** `badCrypto()` é um loop de 10.000 iterações de base64 que retorna os 10 primeiros caracteres — não é hash criptográfico. O seed inicial (`'123456'` em AppManager.js:68) e a senha do usuário de seed (`'123'` em AppManager.js:18) ficam no código, e o "hash" resultante é trivialmente reversível.
**Impact:** Qualquer vazamento do banco de dados expõe todas as senhas instantaneamente; sem bcrypt/argon2 não há fator de custo que resista a ataque de dicionário.
**Recommendation:** Substituir por `bcrypt.hash()` (pacote `bcrypt`) com salt factor >= 12; remover a senha `'123456'` de default em AppManager.js:68 e forçar campo obrigatório no cadastro.

### [CRITICAL] God Class / God Module
**File:** `src/AppManager.js:4-141`
**Description:** A classe `AppManager` concentra: criação de schema e seed de dados (`initDb`), registro de todas as rotas, validação de entrada, lógica de pagamento, criação de usuário, matrícula, geração de relatório financeiro e audit logging — 8+ responsabilidades numa única classe de 139 linhas.
**Impact:** Impossível testar qualquer parte em isolamento; qualquer mudança numa responsabilidade arrasta risco de regressão em todas as outras.
**Recommendation:** Separar em `models/` (queries), `controllers/` (orquestração), `routes/` (roteamento), `config/` (segredos) e `middlewares/` (erro, auth).

### [HIGH] Authentication Absent
**File:** `src/AppManager.js:80-129`, `src/AppManager.js:131-137`
**Description:** Nenhuma rota possui qualquer verificação de identidade ou papel. A rota `GET /api/admin/financial-report` (linha 80) expõe dados financeiros de todos os usuários sem autenticação. A rota `DELETE /api/users/:id` (linha 131) permite deletar qualquer usuário sem credencial alguma — e sem checar se o requisitante é o próprio usuário ou um admin.
**Impact:** Qualquer usuário anônimo pode acessar dados financeiros ou apagar usuários arbitrários.
**Recommendation:** Implementar guard de autenticação global com allowlist explícita de rotas públicas (playbook T-15); `/api/admin/*` e `DELETE /api/users/:id` devem exigir papel `admin` verificado via token assinado.

### [HIGH] Business Logic Inside Route Handler
**File:** `src/AppManager.js:28-78`
**Description:** O handler `POST /api/checkout` tem 50 linhas executando: parsing de entrada, verificação de curso, busca/criação de usuário, processamento de pagamento, criação de matrícula, registro de pagamento e audit log — tudo inline no callback da rota.
**Impact:** Lógica de checkout impossível de reutilizar ou testar isoladamente; a camada de rota virou um monólito disfarçado.
**Recommendation:** Extrair a lógica para um `CheckoutController` (orquestração) e um `CheckoutService` (regras de negócio); a rota fica somente com parsing e chamada ao controller.

### [HIGH] Global Mutable State
**File:** `src/utils.js:9-10`
**Description:** `let globalCache = {}` e `let totalRevenue = 0` são variáveis de módulo mutáveis exportadas — `globalCache` cresce indefinidamente sem TTL, e `totalRevenue` nunca é atualizado (dead code que ocupa escopo global).
**Impact:** `globalCache` é uma memory leak; estado global mutável cria condições de corrida em ambientes com múltiplas requisições concorrentes e impossibilita testes isolados.
**Recommendation:** Eliminar `totalRevenue`; substituir `globalCache` por solução com TTL (Map com timestamp, ou Redis) encapsulada em módulo de cache próprio.

### [HIGH] No Centralized Error Handling
**File:** `src/AppManager.js:41,48,51,54,57,60,70`
**Description:** Cada callback trata (ou ignora) erros de forma diferente: `res.status(500).send("Erro DB")`, `res.status(500).send("Erro Matrícula")`, `res.status(500).send("Erro Pagamento")`, etc. Não há middleware de erro do Express nem tipagem de exceção.
**Impact:** Formato de erro inconsistente entre endpoints; stack traces ou mensagens internas podem vazar ao cliente dependendo do caminho de erro percorrido.
**Recommendation:** Adicionar middleware de erro centralizado Express (`app.use((err, req, res, next) => {...})`); lançar exceções tipadas nos controllers e capturar em um único lugar.

### [HIGH] Broken Referential Integrity
**File:** `src/AppManager.js:131-136`
**Description:** `DELETE /api/users/:id` executa `DELETE FROM users WHERE id = ?` sem remover ou realocar as linhas dependentes em `enrollments` e `payments`. A própria mensagem de resposta confirma: "as matrículas e pagamentos ficaram sujos no banco."
**Impact:** Linhas órfãs em `enrollments` e `payments` corrompem relatórios financeiros e causam `null`/erros em consultas futuras que fazem JOIN com `users`.
**Recommendation:** Adicionar `ON DELETE CASCADE` nas FKs do schema, ou orquestrar a exclusão em ordem correta no service (payments → enrollments → users).

### [HIGH] Callback Hell
**File:** `src/AppManager.js:37-128`
**Description:** O checkout aninha callbacks em 5 níveis (`db.get` -> `db.get` -> `db.run` -> `db.run` -> `db.run`). O relatório financeiro usa contadores manuais (`coursesPending--; if (coursesPending === 0) res.json(report)`) para sincronizar callbacks paralelos em vez de `Promise.all`.
**Impact:** Ordem de execução frágil, erros silenciosamente engolidos em callbacks intermediários, condição de corrida no relatório quando courses e enrollments terminam fora de ordem.
**Recommendation:** Promisificar o driver sqlite3 (ou migrar para `better-sqlite3`/`sqlite`) e reescrever com `async/await` + `Promise.all` para fan-out.

### [MEDIUM] Missing Input Validation
**File:** `src/AppManager.js:35`
**Description:** O checkout valida apenas presença de campos (`!u || !e || !cid || !cc`) mas não valida tipos, formato de e-mail, se `cid` é inteiro, nem o formato mínimo do cartão além do prefixo.
**Impact:** Payloads malformados causam exceções não tratadas ou comportamento indefinido nos níveis mais profundos do callback hell.
**Recommendation:** Introduzir schema de validação por rota (Joi ou Zod) no middleware antes do handler.

### [MEDIUM] Inconsistent Serialization / DTO
**File:** `src/AppManager.js:135`
**Description:** `DELETE /api/users/:id` responde com `res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.")` (plain text), enquanto os outros endpoints retornam JSON. O texto também admite dados corrompidos ao cliente.
**Impact:** Contrato de resposta inconsistente; cliente precisa tratar dois formatos diferentes dependendo da rota.
**Recommendation:** Padronizar todas as respostas em JSON `{ "message": "..." }`; remover admissão de dado corrompido da mensagem pública.

### [MEDIUM] N+1 Query
**File:** `src/AppManager.js:83-128`
**Description:** O relatório financeiro faz: 1 query em `courses`, e para cada curso: 1 query em `enrollments`, e para cada matrícula: 1 query em `users` + 1 query em `payments` — total de `1 + N + 2xM` queries onde N=cursos e M=matrículas.
**Impact:** Com 100 cursos e 500 matrículas cada, dispara 101.001 queries por requisição; latência crescerá linearmente com o volume de dados.
**Recommendation:** Substituir por um único JOIN: `SELECT c.title, u.name, u.email, p.amount, p.status FROM courses c JOIN enrollments e ON e.course_id = c.id JOIN users u ON u.id = e.user_id JOIN payments p ON p.enrollment_id = e.id`.

### [MEDIUM] Missing Pagination
**File:** `src/AppManager.js:83`
**Description:** `SELECT * FROM courses` sem `LIMIT`/`OFFSET` retorna o catálogo inteiro em uma única resposta, sem parâmetros `?page=` ou `?limit=`.
**Impact:** À medida que o catálogo cresce, a resposta vira gigante, degradando latência do cliente e memória do servidor.
**Recommendation:** Adicionar parâmetros `?page=1&limit=20` com defaults razoáveis; executar `SELECT ... LIMIT ? OFFSET ?`.

### [LOW] Poor Variable Naming
**File:** `src/AppManager.js:29-34`
**Description:** Variáveis de 1–2 caracteres em escopo de 50 linhas: `u` (username), `e` (email), `p` (password), `cid` (course_id), `cc` (credit card number).
**Impact:** Legibilidade prejudicada; `cc` confunde-se facilmente com uma sigla de outro contexto.
**Recommendation:** Renomear para `userName`, `email`, `password`, `courseId`, `cardNumber`.

### [LOW] Logging via console.log with Sensitive Data
**File:** `src/AppManager.js:45`, `src/utils.js:13`
**Description:** `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` (AppManager.js:45) loga número de cartão e chave de gateway de pagamento no stdout sem nível/formato. `utils.js:13` também usa `console.log` sem estrutura.
**Impact:** Número de cartão e chave de produção aparecem em logs, painéis e agregadores de log acessíveis por operações — violação de PCI-DSS.
**Recommendation:** Substituir por logger estruturado (winston/pino) com níveis; nunca logar dados de cartão; redactar a chave de gateway nos logs.

### [LOW] sqlite3 Callback API (OBS-03)
**File:** `src/AppManager.js:1`
**Description:** `require('sqlite3').verbose()` usa a API de callback de projeto de 2013, que é a raiz do callback hell identificado no AP-14.
**Impact:** API obsoleta dificulta o uso de `async/await` nativo e aumenta a complexidade do código.
**Recommendation:** Migrar para `better-sqlite3` (síncrono, mais simples) ou o pacote `sqlite` (wrapper Promise sobre sqlite3).

================================
Total: 16 findings
================================
