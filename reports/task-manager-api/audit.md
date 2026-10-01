================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   17 analyzed | ~600 lines of code

## Summary
CRITICAL: 4 | HIGH: 2 | MEDIUM: 6 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Credentials
**File:** `app.py:13`, `services/notification_service.py:10`
**Description:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` está escrito diretamente no código-fonte. Adicionalmente, `services/notification_service.py:10` contém `self.email_password = 'senha123'` — credencial SMTP também hardcoded.
**Impact:** Qualquer pessoa com acesso ao repositório pode forjar sessões/tokens assinados com a chave e obter acesso ao servidor de e-mail. Segredo versionado no Git não pode ser rotacionado sem reescrita de histórico.
**Recommendation:** Mover `SECRET_KEY` para variável de ambiente `FLASK_SECRET_KEY` lida em `src/config/settings.py`; substituir credenciais SMTP por variáveis `SMTP_USER` e `SMTP_PASSWORD` lidas da mesma fonte.

### [CRITICAL] Weak Password Hash + Password Exposed in Response
**File:** `models/user.py:29`, `models/user.py:16-25`
**Description:** Senhas são armazenadas como MD5 sem salt (`hashlib.md5(pwd.encode()).hexdigest()`). O método `to_dict()` inclui o campo `password` na saída, expondo o hash a qualquer endpoint que serialize o usuário (ex: `POST /users` e `GET /users/<id>`).
**Impact:** MD5 é quebrado em segundos com rainbow tables; qualquer vazamento do banco expõe todas as senhas. O hash retornado na resposta HTTP permite ataques offline sem nem precisar do banco.
**Recommendation:** Substituir por `werkzeug.security.generate_password_hash` / `check_password_hash` (bcrypt interno); remover `password` do `to_dict()`.

### [CRITICAL] Debug Mode Always On
**File:** `app.py:34`
**Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` está hardcoded sem condicional por ambiente, ativando o debugger interativo e o reloader em qualquer host em produção.
**Impact:** O Werkzeug debugger expõe um console Python interativo; vaza stack traces completos e permite execução arbitrária de código no servidor.
**Recommendation:** Controlar via `DEBUG=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'`; nunca ligar `debug=True` em `host='0.0.0.0'` sem essa condicional.

### [CRITICAL] Autenticação Ausente / Token Fake
**File:** `routes/user_routes.py:210`, `routes/user_routes.py:42-90`, `routes/user_routes.py:92-132`, `routes/user_routes.py:119-121`
**Description:** O endpoint `POST /login` retorna `'fake-jwt-token-' + str(user.id)` — um token previsível e não-assinado. Nenhum middleware verifica esse token em qualquer rota. `POST /users` aceita `role='admin'` no body sem autenticação; `PUT /users/<id>` aceita `role` do payload sem checar se o chamador é admin; rotas com id de usuário no path não conferem se o recurso pertence ao chamador.
**Impact:** Qualquer chamador anônimo cria usuários com papel admin; qualquer autenticado se promove a admin via `PUT /users/<id>`; leitura e exclusão de dados de outros usuários sem restrição.
**Recommendation:** Implementar JWT real com `PyJWT`; guard global deny-by-default com allowlist explícita de rotas públicas (`/login`, `/`, `/health`); validar papel `admin` para criação/exclusão de usuários e para escrita dos campos `role`/`active`; checar dono do recurso a partir da identidade do token.

### [HIGH] Lógica de Negócio Dentro de Rotas
**File:** `routes/task_routes.py:12-63`, `routes/report_routes.py:13-101`, `routes/user_routes.py:185-211`
**Description:** As funções de rota acumulam parsing de entrada, validação completa, acesso direto ao banco, cálculo de regras de negócio (overdue, completion_rate, estatísticas) e formatação da resposta — `get_tasks()` tem 52 linhas, `summary_report()` tem 90 linhas. Não existe camada de controller/service separada.
**Impact:** Lógica impossível de testar em isolamento; qualquer reúso exige duplicação; a camada de rota vira um monólito disfarçado.
**Recommendation:** Extrair lógica de negócio para `src/controllers/` (orquestração) e `src/services/` (cálculos reutilizáveis); rota fica com ≤ 10 linhas de binding.

### [HIGH] Ausência de Tratamento de Erro Centralizado
**File:** `routes/task_routes.py:62`, `routes/task_routes.py:151-154`, `routes/user_routes.py:87-90`, `routes/user_routes.py:130-132`
**Description:** Cada handler tem seu próprio bloco `try/except` com formato de resposta de erro diferente; os `except:` nus (sem tipo) engolam qualquer exceção sem logar. Não há `@app.errorhandler` global nem middleware de erro.
**Impact:** Bugs reais ficam invisíveis; formato de erro inconsistente entre endpoints dificulta o cliente; stack traces internos nunca chegam a um sistema de monitoramento.
**Recommendation:** Criar `src/middlewares/error_handler.py` com `@app.errorhandler(Exception)` e exceções tipadas (`NotFoundError`, `ValidationError`); remover os try/except de cada handler.

### [MEDIUM] N+1 Query em GET /tasks
**File:** `routes/task_routes.py:41-57`
**Description:** Para cada tarefa retornada em `GET /tasks`, o loop executa `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` separadamente — duas queries extras por tarefa.
**Impact:** Com N tarefas, são geradas 1 + 2N queries; latência cresce linearmente com o volume da tabela.
**Recommendation:** Usar eager loading: `Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()`.

### [MEDIUM] N+1 Query em summary_report
**File:** `routes/report_routes.py:53-68`
**Description:** `summary_report()` busca todos os usuários e depois, para cada um, executa `Task.query.filter_by(user_id=u.id).all()` dentro do loop.
**Impact:** Com U usuários, são 1 + U queries; relatório torna-se inviável em bancos com muitos usuários.
**Recommendation:** Substituir por uma única query com `GROUP BY user_id` ou usar `joinedload` na query de usuários.

### [MEDIUM] Paginação Ausente
**File:** `routes/task_routes.py:14`, `routes/user_routes.py:10-11`
**Description:** `GET /tasks` e `GET /users` executam `.all()` sem `limit`/`offset` ou parâmetros de paginação.
**Impact:** Com o crescimento da tabela, a resposta fica gigante, degrada a UI e sobrecarrega o banco.
**Recommendation:** Aceitar `?page=` e `?per_page=` e usar `.paginate()` do Flask-SQLAlchemy.

### [MEDIUM] Duplicação de Lógica de Validação
**File:** `routes/task_routes.py:110`, `routes/task_routes.py:177`, `routes/user_routes.py:61`, `routes/user_routes.py:106`, `utils/helpers.py:19-23`
**Description:** A validação de status de task é reescrita em POST e PUT; a regex de e-mail aparece em `user_routes.py:61`, `user_routes.py:106` e `utils/helpers.py:21`; o cálculo de overdue está duplicado em `task_routes.py`, `user_routes.py`, `report_routes.py` e `models/task.py`.
**Impact:** Correção em um lugar não propaga para os outros — divergência silenciosa de regra de negócio.
**Recommendation:** Centralizar em schemas Marshmallow (já presente em `requirements.txt`) e em métodos únicos nos controllers/services.

### [MEDIUM] Bare `except` Engolindo Erros
**File:** `routes/task_routes.py:62`, `routes/task_routes.py:237-238`, `routes/user_routes.py:131`, `routes/report_routes.py:185-187`
**Description:** Múltiplos blocos `except:` sem tipo capturado e sem log do erro real antes de retornar 500.
**Impact:** Bugs reais ficam silenciosos; erros de lógica são mascarados como "erro interno".
**Recommendation:** Especificar `except Exception as e:` e logar `e` com `logger.exception`; ou delegar ao handler centralizado (AP-11).

### [MEDIUM] datetime.utcnow() Deprecated (OBS-01 / OBS-02)
**File:** `models/user.py:14`, `models/task.py:15-16`, `models/category.py:10`, `routes/task_routes.py:31`
**Description:** `datetime.utcnow()` e `default=datetime.utcnow` nos campos `db.Column` estão deprecated desde Python 3.12 e removidos no Python 3.14.
**Impact:** Quebra de compatibilidade em upgrades de Python; o default sem `lambda` captura o valor no import, não por chamada.
**Recommendation:** Substituir por `datetime.now(timezone.utc)` e `default=lambda: datetime.now(timezone.utc)`.

### [LOW] Log via print
**File:** `routes/task_routes.py:149`, `routes/task_routes.py:153`, `routes/user_routes.py:83`, `routes/user_routes.py:148`
**Description:** Ações de negócio (criação, deleção de tasks e usuários) são logadas via `print()` sem nível nem formato estruturado.
**Impact:** Logs perdem-se em stdout sem nível de filtragem; impossível integrar com sistemas de monitoramento.
**Recommendation:** Substituir por `import logging; logger = logging.getLogger(__name__)` com `logger.info(...)`.

### [LOW] Checagem de Tipo com `type()` em vez de `isinstance`
**File:** `routes/task_routes.py:141`, `routes/task_routes.py:211`, `utils/helpers.py:103`
**Description:** `if type(tags) == list:` em vez de `isinstance(tags, list)` — falha com subclasses de `list`.
**Impact:** Comportamento incorreto com subtipos; antipadrão Python.
**Recommendation:** Substituir por `isinstance(tags, list)`.

### [LOW] request.get_json() sem silent=True (OBS-04)
**File:** `routes/task_routes.py:88`, `routes/user_routes.py:44`, `routes/report_routes.py:170`
**Description:** `request.get_json()` sem `silent=True` levanta exceção não tratada quando o Content-Type não é `application/json` (Flask ≥ 2.3).
**Impact:** Requisições malformadas causam 500 em vez de 400.
**Recommendation:** Usar `request.get_json(silent=True)` seguido de validação de schema.

================================
Total: 15 findings
================================
