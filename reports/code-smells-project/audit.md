================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~784 lines of code

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 4 | LOW: 2

## Findings

### [CRITICAL] SQL Injection
**File:** `models.py:28, 47-50, 57-60, 65-67, 92, 109-111, 126-129, 140, 148-150, 163-165, 174, 188, 192, 279-282, 289-298`
**Description:** Virtualmente todas as queries no módulo são construídas por concatenação de strings com dados externos. Exemplos representativos: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))` (linha 28); `cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")` (linha 109–111); `query += " AND (nome LIKE '%" + termo + "%'..."` (linha 289). O parâmetro `id` vem de `request` via controller, `email`/`senha` do corpo do login, e `termo`/`categoria` de query string.
**Impact:** SQL injection completo — qualquer chamador pode exfiltrar todo o banco, bypassar autenticação com `' OR 1=1--`, ou destruir dados. O endpoint de login é vulnerável a bypass direto sem credenciais.
**Recommendation:** substituir todas as queries por prepared statements parametrizados: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`. Usar `?` para todos os parâmetros de usuário, sem exceção.

### [CRITICAL] Hardcoded Credentials
**File:** `app.py:7`, `controllers.py:289`
**Description:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` está escrito literalmente no código-fonte (app.py:7). A mesma string aparece de volta no payload de `/health` como `"secret_key": "minha-chave-super-secreta-123"` (controllers.py:289), sendo servida publicamente a qualquer cliente que chame o endpoint.
**Impact:** a chave está versionada no Git e exposta via HTTP — qualquer pessoa pode forjá-la para assinar sessões/tokens. Depois de publicada, a credencial é irrevogável sem deploy.
**Recommendation:** mover para variável de ambiente `FLASK_SECRET_KEY` lida em `src/config/settings.py`; tornar o boot obrigatoriamente falhar se a variável estiver ausente. Remover o campo `secret_key` da resposta de `/health`.

### [CRITICAL] Plaintext Password Storage
**File:** `models.py:109-111, 122-131`, `database.py:75-83`
**Description:** `criar_usuario` insere a senha recebida sem qualquer hash (`INSERT INTO usuarios ... VALUES ('"+...senha+"'...)`, linha 127). `login_usuario` compara senha em texto plano via SQL (linha 109-111). O seed de `database.py` popula o banco com senhas literais como `"admin123"` e `"123456"` (linhas 75-83). `get_todos_usuarios` retorna o campo `senha` em texto plano no JSON de resposta (models.py:80-86).
**Impact:** qualquer vazamento do banco ou da resposta de `/usuarios` expõe todas as credenciais imediatamente, sem necessidade de quebra. Viola LGPD/GDPR.
**Recommendation:** substituir por `werkzeug.security.generate_password_hash` na criação e `check_password_hash` no login. Nunca retornar o campo de senha em nenhuma resposta da API.

### [CRITICAL] Endpoint de Execução Arbitrária de SQL
**File:** `app.py:47-78`
**Description:** duas rotas administrativas sem autenticação: `/admin/reset-db` (linha 47) apaga todos os dados das quatro tabelas; `/admin/query` (linha 59) recebe um campo `"sql"` no corpo e executa `cursor.execute(query)` diretamente, podendo rodar qualquer instrução SQL fornecida pelo chamador.
**Impact:** qualquer pessoa na rede pode apagar todo o banco ou exfiltrar/alterar qualquer dado com uma única requisição POST sem credenciais. É o pior vetor de ataque disponível na aplicação.
**Recommendation:** remover ambos os endpoints completamente. Se algum utilitário de diagnóstico for necessário em ambiente local, implementar como script CLI separado, nunca como rota HTTP.

### [CRITICAL] Debug Mode Habilitado em Produção
**File:** `app.py:8, 88`, `controllers.py:283-290`
**Description:** `app.config["DEBUG"] = True` (app.py:8) e `app.run(debug=True)` (app.py:88) são incondicionais, sem verificação de variável de ambiente. O endpoint `/health` retorna explicitamente `"debug": True` e `"ambiente": "producao"` na mesma resposta (controllers.py:283-290), confirmando ao atacante que o modo debug está ativo.
**Impact:** o reloader e o debugger interativo do Flask ficam expostos; stack traces completos chegam ao cliente; a combinação com o debugger PIN pode levar a RCE.
**Recommendation:** `app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "false").lower() == "true"`; `app.run(debug=app.config["DEBUG"])`. Remover campos de diagnóstico do output de `/health`.

### [HIGH] Authentication Absent
**File:** `app.py:1-88`, `controllers.py:128-134, 188-220, 222-227`
**Description:** o endpoint `/login` (controllers.py:167-186) retorna um dicionário com dados do usuário, mas **não emite nenhum token** — não existe `jwt.encode` ou qualquer mecanismo de sessão no código. Nenhum middleware de autenticação existe. Todas as rotas — incluindo `/usuarios` (que retorna senhas), `/relatorios/vendas`, `/pedidos` e as rotas `/admin/*` — estão abertas sem qualquer verificação de identidade. Além disso, `criar_pedido` aceita `usuario_id` do corpo da requisição (controllers.py:195), e `listar_pedidos_usuario` usa o id do path sem comparar com a identidade autenticada (controllers.py:222-227).
**Impact:** qualquer cliente anônimo acessa dados sensíveis de todos os usuários, modifica pedidos de terceiros, e cria pedidos em nome de qualquer usuário informando seu `usuario_id`.
**Recommendation:** implementar autenticação JWT deny-by-default (playbook T-15): guard global no app com allowlist explícita de rotas públicas (`/`, `/login`, `/health`); segredo obrigatório no boot; identidade extraída do token, nunca do payload; checagem de dono do recurso no controller.

### [HIGH] God Module
**File:** `models.py:1-315`
**Description:** `models.py` (315 linhas) mistura três responsabilidades distintas: acesso ao banco de dados (queries SQL diretas), lógica de negócio (cálculo de descontos progressivos em `relatorio_vendas` linhas 256-263; validação de estoque em `criar_pedido` linhas 139-146; orquestração transacional de itens linhas 148-167), e serialização de resposta (dicionários montados manualmente em cada função).
**Impact:** impossível testar a lógica de desconto sem banco de dados real; qualquer mudança em serialização exige editar o mesmo arquivo que controla transações.
**Recommendation:** separar em `src/models/` (apenas schema/acesso a dado), `src/controllers/` (orquestração) e serialização em helpers de resposta ou DTOs.

### [HIGH] Global Mutable State
**File:** `database.py:4-12`
**Description:** `db_connection = None` é uma variável global de módulo (linha 4) reatribuída com `global db_connection` dentro de `get_db()` (linha 8). A conexão é compartilhada entre todas as requisições sem controle de thread-safety, exceto pela flag `check_same_thread=False` que desabilita a verificação do SQLite.
**Impact:** condição de corrida sob carga concorrente; testes não conseguem isolar estado de banco entre chamadas; `check_same_thread=False` mascara o problema em vez de resolvê-lo.
**Recommendation:** usar `flask.g` para escopo de conexão por requisição, ou encapsular em classe de repositório com injeção de dependência.

### [HIGH] Missing Centralized Error Handling
**File:** `controllers.py:5-292`
**Description:** cada uma das 14 funções de controller tem seu próprio bloco `try/except Exception as e` retornando `jsonify({"erro": str(e)})`. Não existe middleware de erro centralizado. A exceção capturada é serializada e enviada ao cliente (`str(e)`), incluindo mensagens internas do SQLite.
**Impact:** formato de erro inconsistente entre endpoints; mensagens de erro do banco de dados chegam ao cliente, fornecendo informação sobre a estrutura interna; duplicação de ~30 linhas de código de tratamento de erro.
**Recommendation:** registrar um handler global com `@app.errorhandler(Exception)` que loga internamente e retorna mensagem genérica; criar exceções tipadas (`ProdutoNaoEncontrado`, `EstoqueInsuficiente`) para controle de fluxo.

### [MEDIUM] N+1 Query
**File:** `models.py:171-200, 203-233`
**Description:** `get_pedidos_usuario` e `get_todos_pedidos` abrem um cursor de pedidos e, para cada linha, abrem um segundo cursor para buscar `itens_pedido` (linhas 187-188, 220-221) e um terceiro para buscar o nome do produto de cada item (linhas 192-193, 224-225). Para N pedidos com M itens cada, são executadas `1 + N + N*M` queries.
**Impact:** latência cresce linearmente com o volume de pedidos; em produção com centenas de pedidos, o endpoint de listagem se torna inviável.
**Recommendation:** substituir pelos cursores aninhados por um único JOIN: `SELECT p.*, ip.*, pr.nome FROM pedidos p JOIN itens_pedido ip ON ip.pedido_id = p.id JOIN produtos pr ON pr.id = ip.produto_id WHERE p.usuario_id = ?`.

### [MEDIUM] Missing Pagination
**File:** `models.py:6-22, 203-233`
**Description:** `get_todos_produtos()` executa `SELECT * FROM produtos` sem `LIMIT`/`OFFSET` (linha 7); `get_todos_pedidos()` faz o mesmo para pedidos (linha 206). Nenhum endpoint de listagem aceita parâmetros `?page=` ou `?limit=`.
**Impact:** com o crescimento da base de dados, respostas ilimitadas degradam performance do banco e saturação de memória/rede.
**Recommendation:** adicionar `LIMIT ? OFFSET ?` com valores vindos de query params (`page`, `per_page`), com defaults razoáveis (ex.: `per_page=20, max=100`).

### [MEDIUM] Duplicated Validation Logic
**File:** `controllers.py:24-55, 64-92`
**Description:** a validação de campos de produto (nome obrigatório, preço obrigatório, estoque obrigatório, preço ≥ 0, estoque ≥ 0, comprimento de nome) é copiada integralmente entre `criar_produto` (linhas 24-55) e `atualizar_produto` (linhas 64-92). A lista `categorias_validas` também é um literal repetido.
**Impact:** regra de negócio diverge silenciosamente quando corrigida em um handler e esquecida no outro.
**Recommendation:** extrair para um schema de validação compartilhado (Marshmallow ou Pydantic) ou função `validar_payload_produto(dados)` reutilizada pelos dois handlers.

### [MEDIUM] Referential Integrity Broken
**File:** `models.py:65-70`, `database.py:14-52`
**Description:** `deletar_produto` executa `DELETE FROM produtos WHERE id = ?` sem remover ou tratar as linhas dependentes em `itens_pedido` que referenciam `produto_id`. O schema em `database.py` não define `FOREIGN KEY` nem `ON DELETE CASCADE` entre as tabelas.
**Impact:** após deletar um produto, os itens de pedidos existentes ficam com `produto_id` órfão; consultas subsequentes retornam `"Desconhecido"` no nome do produto (models.py:194), introduzindo inconsistência silenciosa nos dados.
**Recommendation:** adicionar `FOREIGN KEY(produto_id) REFERENCES produtos(id) ON DELETE RESTRICT` ou, se deleção lógica for aceita, usar soft-delete com campo `ativo`.

### [LOW] Log via print
**File:** `controllers.py:8, 106, 161, 179, 208-210, 247-250`
**Description:** informações operacionais e de negócio são emitidas via `print()` puro (ex.: `print("Listando " + str(len(produtos)) + " produtos")`, `print("ENVIANDO EMAIL: ...")`, `print("NOTIFICAÇÃO: ...")`), sem nível, timestamp ou estrutura.
**Impact:** sem nível de log, não é possível filtrar ruído em produção; sem timestamp, correlação de eventos é impossível; a chamada `print` bloqueia a thread em alguns ambientes de deploy.
**Recommendation:** substituir por `import logging; logger = logging.getLogger(__name__)` e usar `logger.info(...)` / `logger.error(...)`.

### [LOW] request.get_json() Without silent=True (OBS-04)
**File:** `controllers.py:26, 66, 148, 169, 190, 239`, `app.py:61`
**Description:** `request.get_json()` é chamado sem o parâmetro `silent=True` em 7 pontos. No Flask ≥ 2.3, quando o body não é JSON válido ou o `Content-Type` está ausente, o método lança `BadRequest` não tratada, que vaza stack trace ao cliente.
**Impact:** requisição com body malformado gera resposta 400 com mensagem interna do Werkzeug antes do handler de erro da aplicação.
**Recommendation:** usar `request.get_json(silent=True)` e verificar `if dados is None` explicitamente, ou adotar um schema validator (Marshmallow) que cuida do parsing.

================================
Total: 15 findings
================================
