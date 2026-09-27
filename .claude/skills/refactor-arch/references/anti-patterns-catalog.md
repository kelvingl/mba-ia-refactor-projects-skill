# Catálogo de Anti-Patterns

Catálogo de consulta para a **Fase 2**. Organizado por **categoria** (não por severidade
— a severidade vai marcada em cada item e é fixa, não reclassifique por contexto). Para
cada entrada: sinais de detecção concretos (o que procurar via leitura/`grep`), impacto
e recomendação.

> **Como usar:** varra as 5 categorias abaixo — inclusive "APIs Obsoletas", que é
> obrigatória. Ao bater um sinal, registre **arquivo + linha exata** como finding, com a
> severidade indicada aqui.

---

## 1. Segurança

### AP-01 — SQL Injection (concatenação/interpolação em query)
**Severidade:** CRITICAL
**Sinais:** `cursor.execute("... " + var)`; `cursor.execute(f"SELECT ... {var}")`; em Node, ``` `SELECT * FROM t WHERE id=${id}` ``` ou `db.run("... " + var)`; qualquer query montada com dado vindo de `request.body`/`req.params`/`req.query`.
**Impacto:** execução de SQL arbitrário — vazamento de dados, bypass de autenticação, DROP de tabelas.
**Recomendação:** queries parametrizadas (`cursor.execute("... WHERE id = ?", (id,))`), prepared statements ou ORM.

### AP-02 — Credenciais/Segredos hardcoded
**Severidade:** CRITICAL
**Sinais:** `SECRET_KEY = "..."`, `API_KEY = "..."`, `DB_PASS = "..."`, `paymentGatewayKey = "pk_live_..."` escritos direto no código; padrões `sk_live_`, `pk_live_`, `AKIA*`, `ghp_*`; URL com `user:pass@`; SMTP com senha literal.
**Impacto:** segredo versionado no Git fica exposto a qualquer pessoa com acesso ao repositório.
**Recomendação:** mover para variável de ambiente, lida por um módulo `config/` central.

### AP-03 — Senha em texto plano ou hash obsoleto (MD5/SHA1)
**Severidade:** CRITICAL
**Sinais:** senha do usuário gravada como recebida; `hashlib.md5(pwd)`, `hashlib.sha1(pwd)`, `crypto.createHash('md5')`; hash "artesanal" (loop de base64, XOR manual); campo `password`/`senha` retornado em `to_dict()` ou em `SELECT *` serializado.
**Impacto:** quebra instantânea em qualquer vazamento; risco de conformidade (LGPD/GDPR).
**Recomendação:** `bcrypt`, `argon2` ou `werkzeug.security.generate_password_hash`; nunca devolver o hash na resposta.

### AP-04 — Endpoint de execução arbitrária de código/SQL
**Severidade:** CRITICAL
**Sinais:** rota que recebe `sql`/`query`/`code` no corpo e executa via `eval`, `exec` ou `cursor.execute(input_do_usuario)`; rotas como `/admin/query` ou `/admin/reset-db` sem autenticação.
**Impacto:** um dos piores vetores possíveis — RCE ou SQL injection total.
**Recomendação:** remover o endpoint; se indispensável para debug local, proteger com autenticação forte, allowlist e feature flag desligada em produção.

### AP-05 — Debug/erros verbosos habilitados no caminho de produção
**Severidade:** CRITICAL
**Sinais:** `app.config["DEBUG"] = True` ou `app.run(debug=True)` sem condicional por ambiente; `return jsonify({"erro": str(e)})` expondo detalhe interno; stack trace na resposta.
**Impacto:** vaza estrutura de código, caminhos e versões de biblioteca — insumo direto para reconhecimento de atacante.
**Recomendação:** flag de debug controlada por variável de ambiente; em produção, logar internamente e responder mensagem genérica.

### AP-06 — Autenticação fraca ou ausente
**Severidade:** HIGH
**Sinais:** login retornando token fake (`"fake-jwt-token-" + id`); rota administrativa sem checagem de papel/role; ausência de middleware de autenticação em rota sensível.
**Impacto:** qualquer usuário anônimo alcança funcionalidade administrativa.
**Recomendação:** JWT (ou equivalente) com segredo em variável de ambiente + middleware de `require_auth`/`require_role`.

### AP-07 — Validação de entrada ausente na rota
**Severidade:** MEDIUM
**Sinais:** leitura direta de `req.body.x`/`request.json` sem checar tipo/presença; `request.args.get('page')` convertido para `int` sem tratamento de erro; endpoint aceitando qualquer formato de payload.
**Impacto:** exceções não tratadas, comportamento indefinido com payload malformado.
**Recomendação:** schema de entrada por rota (Pydantic, Marshmallow, Joi, Zod).

## 2. Arquitetura / MVC

### AP-08 — God Class / God Module
**Severidade:** CRITICAL
**Sinais:** arquivo único com mais de ~200 linhas misturando query SQL, validação, regra de negócio, roteamento e formatação; classe com mais de 8 responsabilidades (ex.: `AppManager` que inicializa DB, registra rota, processa pagamento e monta relatório).
**Impacto:** impossível testar em isolamento; qualquer mudança tem alto risco de regressão em outra parte do sistema.
**Recomendação:** separar em camadas (model / controller / view) organizadas por domínio.

### AP-09 — Lógica de negócio dentro de rota/controller
**Severidade:** HIGH
**Sinais:** handler de rota com mais de ~30 linhas fazendo parsing + validação + query + cálculo + resposta; 15+ `if`s encadeados de validação dentro do handler.
**Impacto:** lógica impossível de reaproveitar ou testar isoladamente; a camada de rota vira um monolito disfarçado.
**Recomendação:** validação para schema/middleware, regra de negócio para controller/service, rota fica só roteando.

### AP-10 — Estado global mutável
**Severidade:** HIGH
**Sinais:** `global db_connection`; variável de módulo tipo `let totalRevenue = 0` ou `globalCache = {}`; cache sem TTL que cresce indefinidamente; conexão de banco guardada em variável global em vez de factory.
**Impacto:** condição de corrida, testes não isolados, comportamento diferente entre execuções.
**Recomendação:** encapsular em classe com escopo por requisição, injeção de dependência ou factory.

### AP-11 — Ausência de tratamento de erro centralizado
**Severidade:** HIGH
**Sinais:** `try/except Exception` repetido em cada função de controller, cada um formatando a resposta de erro à sua maneira; ausência de middleware de erro no Express; stack trace vazando para o cliente.
**Impacto:** duplicação generalizada; formato de erro inconsistente entre endpoints.
**Recomendação:** handler central (Flask `errorhandler`, middleware do Express) + exceções tipadas.

### AP-12 — Serialização/DTO inconsistente
**Severidade:** MEDIUM
**Sinais:** `to_dict()` do model difere do dicionário montado manualmente na rota; alguns endpoints retornam `{"dados": ...}` e outros a lista crua; resposta em string solta (`res.send("Usuário deletado")`) em vez de JSON.
**Impacto:** contrato de resposta imprevisível para quem consome a API.
**Recomendação:** padronizar serializers e o envelope de resposta.

## 3. Dados e Performance

### AP-13 — Integridade referencial quebrada
**Severidade:** HIGH
**Sinais:** `DELETE FROM users WHERE id = ?` sem remover/realocar linhas dependentes em outras tabelas; comentário/resposta admitindo dado "sujo" no banco; ausência de `ON DELETE CASCADE` ou rotina de limpeza equivalente.
**Impacto:** chaves estrangeiras órfãs; consultas futuras retornam dado corrompido ou inconsistente.
**Recomendação:** cascade no schema, ou um service que orquestra a exclusão na ordem correta.

### AP-14 — Callback hell / ausência de sincronização de promises
**Severidade:** HIGH
**Sinais (Node.js):** callbacks aninhados em mais de 3 níveis; contadores manuais (`pendingX--; if (pendingX === 0) ...`) em vez de `Promise.all`; múltiplas chamadas assíncronas sem `async/await`.
**Impacto:** ordem de execução frágil, condição de corrida, erro perdido silenciosamente.
**Recomendação:** promisificar o driver e reescrever com `async/await` + `Promise.all` para fan-out.

### AP-15 — Query N+1
**Severidade:** MEDIUM
**Sinais:** loop que dispara uma query por iteração (`for row in rows: cursor.execute(... row.id ...)`; `for t in tasks: User.query.get(t.user_id)`); cursores aninhados dentro de `for`.
**Impacto:** latência cresce linearmente com o volume de dados; risco real de timeout em produção.
**Recomendação:** JOIN na query principal ou eager loading do ORM (`joinedload`, `include`, `populate`).

### AP-16 — Paginação ausente / resposta sem limite
**Severidade:** MEDIUM
**Sinais:** `GET /recurso` executando `.all()`/`SELECT *` sem `limit`/`offset`; ausência de parâmetros `?page=`/`?limit=`.
**Impacto:** resposta gigante degrada a UI e sobrecarrega o banco à medida que a tabela cresce.
**Recomendação:** paginação por `limit`/`offset` ou cursor.

### AP-17 — Duplicação de lógica de validação
**Severidade:** MEDIUM
**Sinais:** a mesma regra (`if priority < 1 or priority > 5`) repetida em `POST`, `PUT` e num helper; regex de e-mail copiado em mais de um lugar; lista de status válidos reescrita como literal em vários pontos.
**Impacto:** correções feitas em um lugar e esquecidas no outro — divergência silenciosa de regra de negócio.
**Recomendação:** extrair para schema (Pydantic/Marshmallow/Joi) ou função de validação compartilhada.

### AP-18 — `except`/`catch` genérico engolindo erro
**Severidade:** MEDIUM
**Sinais:** `try: ... except: pass`; `except:` sem tipo; `catch (e) {}` vazio.
**Impacto:** bug real fica invisível; erro é mascarado em vez de tratado.
**Recomendação:** capturar exceção específica e logar antes de decidir o que fazer.

## 4. Qualidade e Legibilidade

### AP-19 — Números/strings mágicas
**Severidade:** LOW
**Sinais:** `if faturamento > 10000`, `priority == 3`, status espalhado como string literal (`'pending'`, `'done'`) em vários arquivos.
**Recomendação:** constantes nomeadas ou enum.

### AP-20 — Nomenclatura de variável pobre
**Severidade:** LOW
**Sinais:** variáveis de 1–2 caracteres em escopo grande (`u`, `e`, `p`, `cid`, `cc`, `t`).
**Recomendação:** nomes descritivos a partir de escopos com mais de ~5 linhas.

### AP-21 — Log via `print`/`console.log`
**Severidade:** LOW
**Sinais:** `print(...)` em handler de produção; `console.log` sem nível/formato.
**Recomendação:** logger estruturado com níveis (`logging`, `winston`, `pino`).

### AP-22 — Concatenação manual de string para mensagem
**Severidade:** LOW
**Sinais:** `"Listando " + str(len(produtos)) + " produtos"` em vez de f-string/template literal.
**Recomendação:** f-string/template literal — idealmente já passando pelo logger.

### AP-23 — Checagem de tipo por comparação em vez de `isinstance`
**Severidade:** LOW
**Sinais (Python):** `if type(tags) == list:` em vez de `isinstance(tags, list)`.
**Recomendação:** `isinstance(tags, list)`.

## 5. APIs Obsoletas (verificação obrigatória)

Esta categoria **não pode ser pulada** — rode a checagem mesmo que nada mais tenha sido
encontrado ainda.

| ID | Sinal | Severidade | Substituto recomendado |
|---|---|---|---|
| OBS-01 | `datetime.utcnow()` (deprecated desde Python 3.12) | MEDIUM | `datetime.now(timezone.utc)` |
| OBS-02 | `default=datetime.utcnow` em `db.Column` | MEDIUM | `default=lambda: datetime.now(timezone.utc)` |
| OBS-03 | `require('sqlite3').verbose()` com API de callback em projeto novo | LOW | `better-sqlite3` (síncrono) ou `sqlite` (promises) |
| OBS-04 | `request.get_json()` sem `silent=True` (Flask ≥ 2.3) | LOW | `request.get_json(silent=True)` + schema validator |
| OBS-05 | `try: datetime.strptime(...) except:` sem tipo | LOW | `except ValueError:` |
| OBS-06 | `require('body-parser')` em Express 4.16+ | LOW | `express.json()` / `express.urlencoded()` |
| OBS-07 | `SQLALCHEMY_TRACK_MODIFICATIONS` ausente da config | LOW | setar explicitamente `False` |
| OBS-08 | `flask_sqlalchemy` < 3.0 em `requirements.txt` | LOW | atualizar para a linha 3.x |

---

## Checklist antes de fechar a Fase 2

- [ ] Cobri as 5 categorias (Segurança, Arquitetura/MVC, Dados/Performance, Qualidade, APIs Obsoletas)?
- [ ] A checagem de APIs Obsoletas (OBS-01 a OBS-08) foi feita, mesmo que nada tenha sido encontrado?
- [ ] Cada finding tem arquivo + linha?
- [ ] Tenho ≥ 5 findings, com ≥ 1 CRITICAL ou HIGH?

Se alguma resposta for "não", volte ao código antes de fechar o relatório.
