================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   15 analyzed | ~700 lines of code

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 5 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Credentials
**File:** `app.py:13`, `services/notification_service.py:7-10`
**Description:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` está hardcoded no bootstrap da aplicação. Em `notification_service.py`, credenciais SMTP literais incluem `email_host = 'smtp.gmail.com'`, `email_user = 'taskmanager@gmail.com'` e `email_password = 'senha123'`.
**Impact:** Qualquer pessoa com acesso ao repositório pode forjar tokens de sessão com a SECRET_KEY; as credenciais do servidor SMTP ficam expostas no histórico Git permanentemente.
**Recommendation:** Mover `SECRET_KEY`, `SMTP_HOST`, `SMTP_USER` e `SMTP_PASSWORD` para variáveis de ambiente lidas em `src/config/settings.py`; falhar o boot com mensagem clara se qualquer segredo obrigatório estiver ausente.

### [CRITICAL] Weak Password Hash + Hash Exposed in Response
**File:** `models/user.py:29`, `models/user.py:21`
**Description:** `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()` para armazenar senhas. Adicionalmente, `to_dict()` inclui `'password': self.password` na linha 21, expondo o hash MD5 em todas as respostas que serializam o usuário — incluindo `GET /users/<id>` e `POST /login`.
**Impact:** MD5 é reversível por rainbow tables em segundos; o hash exposto na resposta elimina a necessidade de quebrar o armazenamento diretamente. Risco direto de conformidade LGPD/GDPR.
**Recommendation:** Substituir por `werkzeug.security.generate_password_hash` / `check_password_hash` (bcrypt interno); remover o campo `password` de `to_dict()`.

### [CRITICAL] Debug Mode Always Enabled
**File:** `app.py:34`
**Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` sem condicional por variável de ambiente. Em modo debug, o Flask expõe o debugger interativo Werkzeug e stack traces completos ao cliente em qualquer erro.
**Impact:** Vaza estrutura interna do código, caminhos de arquivo e versões de biblioteca; o debugger Werkzeug permite execução de código arbitrário via PIN se acessível na rede.
**Recommendation:** `debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'`; em produção, servir via gunicorn sem a flag debug.

### [HIGH] Weak Authentication — Fake Token, No Guard, IDOR, Role Escalation
**File:** `routes/user_routes.py:210`, `routes/user_routes.py:119-125`, `routes/task_routes.py:105`, `routes/user_routes.py:27`, `routes/user_routes.py:92-131`, `routes/user_routes.py:134-151`
**Description:** `POST /login` emite `'fake-jwt-token-' + str(user.id)` (linha 210), não um JWT verificável. Nenhuma rota valida esse token — não existe middleware de autenticação em nenhum blueprint. Consequências: (1) qualquer usuário anônimo pode criar, atualizar e deletar usuários; (2) `PUT /users/<id>` aceita `role` e `active` do payload sem checar quem é o solicitante (linhas 119–125), permitindo que qualquer um se promova a admin; (3) `user_id` na criação de tarefa vem do corpo da requisição (linha 105), não da identidade autenticada; (4) `GET/PUT/DELETE /users/<user_id>` e `GET /users/<user_id>/tasks` não comparam o id do path com a identidade do token (IDOR).
**Impact:** Qualquer usuário anônimo alcança todas as operações destrutivas; qualquer usuário autenticado se promove a admin; dados de qualquer usuário ficam acessíveis ou modificáveis sem autenticação.
**Recommendation:** Guard deny-by-default (T-15): middleware global que valida JWT real em todas as rotas salvo allowlist pública (`/`, `/health`, `/login`); usar `PyJWT` com `SECRET_KEY` obrigatória no boot; somente admin pode gravar `role`/`active`; `user_id` de tarefas vem do token, não do payload; controllers verificam dono do recurso.

### [HIGH] Business Logic in Routes
**File:** `routes/task_routes.py:11-62`, `routes/report_routes.py:13-101`
**Description:** `get_tasks()` tem 50 linhas calculando status overdue, disparando N+1 queries e montando dicionários manualmente. `summary_report()` tem 88 linhas com todas as queries de agregação e cálculos de produtividade por usuário embutidos diretamente no handler de rota.
**Impact:** Lógica impossível de reaproveitar ou testar em isolamento; a camada de roteamento vira um monolito disfarçado.
**Recommendation:** Extrair lógica de negócio para controllers/services; a rota fica responsável apenas por deserializar o request, chamar o controller e retornar a resposta serializada.

### [HIGH] No Centralized Error Handling
**File:** `routes/task_routes.py:146-153`, `routes/user_routes.py:80-90`, `routes/report_routes.py:183-188`
**Description:** Cada handler de rota tem seu próprio bloco `try/except` com mensagens de erro não uniformes (`'Erro ao criar usuário'`, `'Erro interno'`, `'Erro ao atualizar'`). Nenhum `@app.errorhandler` está registrado em `app.py`.
**Impact:** Formato de erro inconsistente entre endpoints; exceções específicas são silenciadas; bugs reais ficam invisíveis nos logs.
**Recommendation:** Registrar `@app.errorhandler(Exception)` em `app.py` com envelope de resposta padronizado (`{'error': ..., 'code': ...}`); usar exceções de domínio tipadas capturadas no handler central.

### [HIGH] Broken Referential Integrity on Category Delete
**File:** `routes/report_routes.py:211-222`
**Description:** `DELETE /categories/<cat_id>` remove a categoria sem tratar as tarefas que a referenciam via `category_id`. O model `Task` define `db.ForeignKey('categories.id', nullable=True)` sem `cascade` ou rotina de limpeza na rota.
**Impact:** Após a deleção de uma categoria, tarefas ficam com `category_id` apontando para um registro inexistente; consultas subsequentes retornam dados inconsistentes.
**Recommendation:** Adicionar `cascade='all, delete-orphan'` no relacionamento do model `Category`, ou executar `Task.query.filter_by(category_id=cat_id).update({'category_id': None})` antes de deletar.

### [MEDIUM] N+1 Query on Task Listing
**File:** `routes/task_routes.py:41-57`
**Description:** `get_tasks()` carrega todas as tarefas com `Task.query.all()` e, dentro do loop, dispara `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` por tarefa — produzindo 2N queries extras para N tarefas.
**Impact:** Latência cresce linearmente com o número de tarefas; em produção com centenas de registros, a rota se torna um gargalo de banco de dados.
**Recommendation:** Eager loading: `Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()`.

### [MEDIUM] Missing Pagination on List Endpoints
**File:** `routes/task_routes.py:12`, `routes/user_routes.py:11`
**Description:** `GET /tasks` e `GET /users` executam `.query.all()` sem limite ou offset, retornando todos os registros de uma vez.
**Impact:** Resposta degrada à medida que a tabela cresce; risco de timeout e sobrecarga de memória em produção.
**Recommendation:** Adicionar parâmetros `?page=` e `?per_page=` com `.paginate()` do Flask-SQLAlchemy.

### [MEDIUM] Duplicate Validation Logic
**File:** `routes/task_routes.py:110-111`, `routes/task_routes.py:177-183`, `utils/helpers.py:75-88`
**Description:** Validação de status (`['pending','in_progress','done','cancelled']`) e prioridade (range 1–5) reescrita como literal em `create_task`, `update_task` e `process_task_data` em `helpers.py` (função nunca usada pelas rotas). Regex de email duplicada em `user_routes.py:61` e `utils/helpers.py:20-23`.
**Impact:** Regra corrigida em um ponto e esquecida nos demais — divergência silenciosa de regra de negócio.
**Recommendation:** Centralizar em schemas Marshmallow (dependência já presente) ou nas constantes definidas em `utils/helpers.py:110-116`.

### [MEDIUM] Deprecated datetime.utcnow() — OBS-01 + OBS-02
**File:** `models/user.py:14`, `models/task.py:16-17`, `models/category.py:8`, `routes/task_routes.py:31`
**Description:** `datetime.utcnow()` foi marcado deprecated no Python 3.12 e aparece como chamada direta nas rotas e como default de coluna ORM (`default=datetime.utcnow`) em todos os models.
**Impact:** Deprecation warnings em Python 3.12+; remoção prevista em versão futura da linguagem.
**Recommendation:** Substituir por `datetime.now(timezone.utc)` nas chamadas diretas; nos defaults de coluna usar `default=lambda: datetime.now(timezone.utc)`.

### [MEDIUM] Bare except Clauses
**File:** `routes/task_routes.py:138`, `routes/task_routes.py:204`, `routes/user_routes.py:128-132`, `routes/user_routes.py:146-151`
**Description:** Múltiplos blocos `except:` sem tipo de exceção nas conversões de data e operações de banco — captura inclusive `SystemExit` e `KeyboardInterrupt`, além de ocultar o tipo real da falha.
**Impact:** Bugs reais ficam mascarados; o comportamento em produção diverge do esperado em desenvolvimento sem nenhum sinal visível.
**Recommendation:** Usar tipos específicos: `except ValueError:` nas conversões de data, `except SQLAlchemyError:` nas operações de banco.

### [LOW] Type Check via type() Instead of isinstance()
**File:** `routes/task_routes.py:141`, `routes/task_routes.py:210`, `utils/helpers.py:103`
**Description:** Checagem de tipo feita com `if type(tags) == list:` em três lugares, em vez de `isinstance(tags, list)`.
**Impact:** Falha silenciosa com subclasses de list; viola o estilo idiomático Python.
**Recommendation:** Substituir por `isinstance(tags, list)`.

### [LOW] Logging via print()
**File:** `routes/user_routes.py:83-89`, `routes/task_routes.py:149`, `routes/task_routes.py:219`
**Description:** Eventos de negócio (criação, atualização e deleção de entidades) são registrados via `print()` direto, sem nível de log ou timestamp estruturado.
**Impact:** Impossível filtrar por nível em produção; output vai para stdout sem formatação consistente; sem integração com sistemas de observabilidade.
**Recommendation:** Substituir por `app.logger.info(...)` ou `logging.getLogger(__name__)` com nível configurável por variável de ambiente.

================================
Total: 14 findings
================================
