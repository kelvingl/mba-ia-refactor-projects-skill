================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~400 lines of code

## Summary
CRITICAL: 6 | HIGH: 3 | MEDIUM: 2 | LOW: 1

## Findings

### [CRITICAL] SQL Injection — String Concatenation in Query
**File:** `models.py:28`
**Description:** `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))` — construção de query via concatenação de string. O mesmo padrão se repete em múltiplas funções (criar_produto, atualizar_produto, deletar_produto, buscar_produtos) onde parâmetros vêm de user input.
**Impact:** SQL injection direto — atacante pode forjar queries arbitrárias, acessar/modificar/deletar dados ilicitamente, ou causar negação de serviço.
**Recommendation:** Substituir todas as queries por prepared statements com placeholders: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`.

### [CRITICAL] Hardcoded Credentials — SECRET_KEY
**File:** `app.py:7`
**Description:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` está hardcoded no código. A mesma chave aparece também como campo `secret_key` na resposta de `/health` (controllers.py:289), sendo retornada ao cliente.
**Impact:** Qualquer pessoa com acesso ao repositório ou ao endpoint `/health` pode forjar sessões/tokens assinados com essa chave. Viola OWASP Top 10 — Broken Authentication.
**Recommendation:** Mover para variável de ambiente `FLASK_SECRET_KEY` lida em `config/settings.py`. Remover do output de `/health`.

### [CRITICAL] Password in Plaintext — Login without Hashing
**File:** `models.py:105-120`
**Description:** `login_usuario()` compara senha direto em texto plano: `WHERE email = '" + email + "' AND senha = '" + senha + "'"`. Não há hash. Além disso, `get_todos_usuarios()` e `get_usuario_por_id()` retornam o campo `"senha"` na serialização (linhas 84, 99), expondo hashes (se houvesse) ou texto plano (como é agora) ao cliente.
**Impact:** Vazamento instantâneo de todas as senhas em qualquer breach do banco; risco de acesso não autorizado; violação LGPD/GDPR.
**Recommendation:** Usar `werkzeug.security.generate_password_hash()` no insert e `werkzeug.security.check_password_hash()` no login. Nunca retornar `"senha"` em nenhuma resposta JSON.

### [CRITICAL] Unauthenticated Arbitrary Code/SQL Execution
**File:** `app.py:59-78`
**Description:** Rota `/admin/query` (POST) aceita parâmetro `sql` do corpo e executa diretamente via `cursor.execute(query)` — sem autenticação, sem validação, sem allowlist. RCE/SQL injection total.
**Impact:** Um dos piores vetores — atacante remoto pode executar qualquer SQL, dropar tabelas, ler/modificar dados, resetar senhas administrativas.
**Recommendation:** Remover o endpoint inteiramente (é ferrament de debug insegura). Se absolutamente necessário para testes locais, proteger com middleware de autenticação forte, usar allowlist de queries pré-aprovadas e feature flag desligada em produção.

### [CRITICAL] Debug Mode Enabled in Production
**File:** `app.py:8`
**Description:** `app.config["DEBUG"] = True` sem condicional por ambiente. Também `app.run(debug=True)` na linha 88. Além disso, controllers.py:288 retorna `"debug": True` como campo em `/health`.
**Impact:** Debug mode vaza stack traces completos, caminhos de arquivo, versões de biblioteca — insumo valioso para reconhecimento de atacante. Debugger interativo fica acessível em produção.
**Recommendation:** Controlar via variável de ambiente: `DEBUG = os.getenv("FLASK_DEBUG", "False") == "True"`. Em produção, sempre `False`. Remover campo `debug` do output de `/health`.

### [CRITICAL] God Module — Mixed Responsibilities
**File:** `models.py` (1-315)
**Description:** Arquivo único concentra toda lógica de negócio: validação (implícita), acesso a dados (todas as queries), orquestração de pedidos (loops, cálculos de estoque), e serialização (dicts manuais). Sem separação de camadas.
**Impact:** Impossível testar em isolamento; qualquer mudança tem risco alto de regressão; duplicação de validação entre controller e model; legibilidade zero em projetos maiores.
**Recommendation:** Separar em `models/` (entidades puras), `controllers/` (orquestração), `services/` (regra de negócio), e `repositories/` (acesso a dados com queries parametrizadas).

### [HIGH] Global Mutable State — Database Connection
**File:** `database.py:4`
**Description:** `db_connection = None` como variável global. Inicializada uma vez em `get_db()` e reutilizada em todo o código. Sem sincronização, sem per-request pooling.
**Impact:** Condição de corrida em concorrência; testes não isolados; comportamento diferente entre execuções; impossível ter múltiplas conexões independentes.
**Recommendation:** Encapsular em classe com factory pattern ou usar `Flask.g` para per-request singleton. Ou usar `flask-sqlalchemy` que gerencia pool automaticamente.

### [HIGH] N+1 Query Problem — Loop with Query per Item
**File:** `models.py:187-199`
**Description:** `get_pedidos_usuario()` dispara uma query extra por item de pedido (`for item in itens: cursor3.execute(...)`). Para um pedido com 5 itens = 3 queries (1 pedido + 5 itens + 5 produtos). Padrão idêntico em `get_todos_pedidos()` linhas 219-231.
**Impact:** Latência cresce linearmente com volume de dados. Um relatório de 1000 pedidos com 5 itens cada = 6000 queries em vez de 2. Timeout em produção.
**Recommendation:** Reescrever com JOINs: `SELECT p.*, ip.*, pr.nome FROM pedidos p LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id LEFT JOIN produtos pr ON pr.id = ip.produto_id WHERE p.usuario_id = ?`.

### [HIGH] Nested Cursors in Loop
**File:** `models.py:219-231`
**Description:** `get_todos_pedidos()` abre `cursor2` e `cursor3` dentro de loops aninhados. SQLite aguenta, mas é anti-pattern perigoso — em bancos concorrentes causa deadlock ou esgota pool de conexões.
**Impact:** Risco de deadlock em produção; esgotamento de pool de conexão; latência O(n³) em dados grandes.
**Recommendation:** Usar um JOIN único em vez de cursores aninhados. Ou if impossível, carregar tudo em memória antes do loop.

### [MEDIUM] Duplicate Validation Logic
**File:** `controllers.py:24-62` e `controllers.py:64-96`
**Description:** Validação de nome/preco/estoque repetida idêntica em `criar_produto()` e `atualizar_produto()`. Mesmo padrão se repete em usuários.
**Impact:** Correções de regra de negócio feitas em um lugar e esquecidas no outro — divergência silenciosa.
**Recommendation:** Extrair para schema Pydantic ou função de validação compartilhada.

### [LOW] Magic Numbers — Hardcoded Thresholds
**File:** `models.py:256-262`
**Description:** Desconto baseado em faturamento com thresholds hardcoded: `if faturamento > 10000`, `> 5000`, `> 1000`. Mesmos valores aparecem em comentários ou não — impossível saber se estão sincronizados com regras de negócio.
**Impact:** Mudança de política de desconto força edição de código e re-deployment.
**Recommendation:** Extrair para constantes nomeadas ou tabela de configuração.

================================
Total: 10 findings
================================
