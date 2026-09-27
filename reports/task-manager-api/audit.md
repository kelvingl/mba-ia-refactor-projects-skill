================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 + SQLAlchemy 3.1.1
Files:   13 analyzed | ~650 lines of code

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Credentials — SECRET_KEY
**File:** `app.py:13`
**Description:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` está hardcoded diretamente no bootstrapping da aplicação, sem leitura de variável de ambiente.
**Impact:** Qualquer pessoa com acesso ao repositório pode forjar tokens/sessões assinadas com essa chave; segredo comprometido para sempre após o primeiro push.
**Recommendation:** Mover para variável de ambiente `SECRET_KEY` carregada via `python-dotenv` em um módulo `src/config/settings.py`; remover o literal do código.

### [CRITICAL] Hardcoded Credentials — SMTP Password
**File:** `services/notification_service.py:9-10`
**Description:** `self.email_user = 'taskmanager@gmail.com'` e `self.email_password = 'senha123'` estão hardcoded no construtor de `NotificationService`; credenciais de e-mail ficam versionadas no Git.
**Impact:** Credenciais de e-mail expostas a qualquer pessoa com acesso ao repositório; conta Gmail comprometida.
**Recommendation:** Ler `SMTP_USER` e `SMTP_PASSWORD` de variáveis de ambiente via `os.environ` ou `python-dotenv`.

### [CRITICAL] Weak Password Hash (MD5) + Password Exposed in Response
**File:** `models/user.py:29`, `models/user.py:17-25`
**Description:** `self.password = hashlib.md5(pwd.encode()).hexdigest()` usa MD5 sem sal para armazenar senhas. O método `to_dict()` devolve o campo `'password'` com o hash na resposta, expondo-o para qualquer chamada que serializa o usuário.
**Impact:** MD5 quebra instantaneamente por rainbow tables; hash exposto via API completa o vetor de ataque.
**Recommendation:** Substituir por `werkzeug.security.generate_password_hash` (bcrypt/pbkdf2); remover `'password'` do `to_dict()`.

### [CRITICAL] Debug Mode Unconditionally Enabled
**File:** `app.py:34`
**Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` habilita o modo debug sem checar a variável de ambiente — em produção, o Werkzeug debugger fica exposto e stack traces vazam para o cliente.
**Impact:** Debugger interativo acessível remotamente (`0.0.0.0`); qualquer exceção devolve stack trace completo, revelando caminhos de arquivo, versões e estrutura interna.
**Recommendation:** Ler `DEBUG` de `os.environ.get('FLASK_DEBUG', 'false')` e passar para `app.run(debug=debug_flag)`.

### [CRITICAL] God Module — Fat Route File
**File:** `routes/task_routes.py:1-300`
**Description:** Módulo único de 300 linhas misturando roteamento, validação de entrada, lógica de negócio (cálculo de `overdue`, contagem de estatísticas), queries N+1 e formatação de resposta em um mesmo arquivo sem separação de camadas.
**Impact:** Impossível testar lógica de negócio isoladamente; qualquer mudança em validação ou cálculo arrisca regressão em endpoints não relacionados.
**Recommendation:** Extrair validação para schemas Marshmallow, lógica de negócio para controllers/services e deixar as rotas apenas roteando.

### [HIGH] Weak/Fake Authentication Token
**File:** `routes/user_routes.py:210`
**Description:** O endpoint `/login` devolve `'token': 'fake-jwt-token-' + str(user.id)` como token de autenticação. Nenhuma rota é protegida por middleware que valide esse token.
**Impact:** Qualquer cliente pode forjar um token válido concatenando o prefixo com qualquer ID; toda a API está efetivamente sem autenticação.
**Recommendation:** Implementar JWT real com `PyJWT`, assinar com `SECRET_KEY` carregada de env, e adicionar decorator `require_auth` às rotas que exigem autenticação.

### [HIGH] Business Logic Inside Route Handlers
**File:** `routes/task_routes.py:12-63`, `routes/report_routes.py:13-101`
**Description:** `get_tasks()` (52 linhas) realiza serialização manual, cálculo de `overdue`, e queries N+1 de usuário e categoria. `summary_report()` (88 linhas) executa 10+ queries individuais, loops com contadores manuais e cálculos de taxa de conclusão direto no handler.
**Impact:** Lógica de negócio não pode ser reutilizada, testada ou compartilhada entre endpoints; a rota vira um monolito embutido.
**Recommendation:** Mover cálculos e orquestração para `controllers/task_controller.py` e `controllers/report_controller.py`; handler fica responsável apenas por parsear request e devolver response.

### [HIGH] Absent Centralized Error Handling
**File:** `routes/task_routes.py:62`, `routes/task_routes.py:222-223`, `routes/user_routes.py:131`, `routes/user_routes.py:149`, `routes/report_routes.py:183`
**Description:** Cada handler tem seu próprio bloco `try/except`, cada um formatando a mensagem de erro de forma diferente ("Erro interno", "Erro ao criar task", "Erro ao atualizar"). Não existe nenhum `@app.errorhandler` global registrado.
**Impact:** Formato de erro inconsistente entre endpoints; qualquer duplicação de tratamento deve ser corrigida em vários lugares simultaneamente.
**Recommendation:** Registrar handler global via `@app.errorhandler(Exception)` em `middlewares/error_handler.py`; remover try/except redundantes dos controllers.

### [HIGH] Brittle Referential Integrity — Manual Cascade
**File:** `routes/user_routes.py:140-143`
**Description:** A exclusão de usuário é feita deletando tasks em loop com `db.session.delete(t)` para cada task, antes de deletar o usuário — sem `ON DELETE CASCADE` no schema nem transação que envolva toda a operação de forma atômica.
**Impact:** Se a exclusão de alguma task falhar no meio do loop, o banco fica inconsistente com tasks sem usuário; a deleção do usuário ocorre fora do `try` que garante o rollback.
**Recommendation:** Adicionar `cascade='all, delete-orphan'` no relacionamento `User.tasks` (SQLAlchemy) ou definir `ON DELETE CASCADE` na FK do schema.

### [MEDIUM] Inconsistent Serialization/DTO
**File:** `routes/task_routes.py:18-28`, `models/task.py:23-36`
**Description:** `get_tasks()` constrói um dicionário manualmente com os mesmos campos de `Task.to_dict()`, porém com campos extras (`overdue`, `user_name`, `category_name`) — mas outros endpoints usam `to_dict()` diretamente. `User.to_dict()` (`models/user.py:17-25`) expõe o hash da senha na resposta.
**Impact:** Contrato de resposta diverge silenciosamente entre endpoints; consumidores da API recebem estruturas inconsistentes.
**Recommendation:** Criar schemas Marshmallow por entidade (`TaskSchema`, `UserSchema`) que excluam campos sensíveis e padronizem a resposta; eliminar dicionários manuais nas rotas.

### [MEDIUM] N+1 Query
**File:** `routes/task_routes.py:41-57`, `routes/report_routes.py:54-68`
**Description:** `get_tasks()` itera todas as tasks e, para cada uma, executa `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` separadamente (2N queries extras). `summary_report()` busca todos os usuários e depois faz `Task.query.filter_by(user_id=u.id).all()` para cada um (N queries extras).
**Impact:** Com 1000 tasks, `GET /tasks` dispara ~2001 queries; latência cresce linearmente com o volume.
**Recommendation:** Usar `joinedload` do SQLAlchemy: `Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()`.

### [MEDIUM] Pagination Absent
**File:** `routes/task_routes.py:14`, `routes/user_routes.py:11`
**Description:** `Task.query.all()` e `User.query.all()` retornam todos os registros sem limite, sem parâmetros `?page=` ou `?limit=`.
**Impact:** Resposta de tamanho ilimitado degrada a UI e sobrecarrega o banco conforme a tabela cresce.
**Recommendation:** Usar `Task.query.paginate(page, per_page)` e retornar metadados de paginação (`total`, `pages`, `current_page`).

### [MEDIUM] Duplicated Validation Logic
**File:** `routes/task_routes.py:110-114`, `routes/task_routes.py:176-184`, `utils/helpers.py:75-88`
**Description:** A validação de `status` (lista `['pending', 'in_progress', 'done', 'cancelled']`) e de `priority` (range 1-5) estão duplicadas literalmente em `create_task`, `update_task` e `process_task_data` — três implementações independentes da mesma regra.
**Impact:** Uma correção na regra de validação exige alteração em pelo menos 3 lugares; divergência silenciosa quando feita em apenas um.
**Recommendation:** Centralizar em um `TaskSchema` Marshmallow com validators e referenciar `VALID_STATUSES` de `utils/helpers.py` (já existe mas não é usado pelas rotas).

### [MEDIUM] Generic Bare `except`
**File:** `routes/task_routes.py:62`, `routes/task_routes.py:137`, `routes/user_routes.py:131`, `routes/user_routes.py:149`
**Description:** Múltiplos blocos `except:` sem tipo específico mascaram qualquer exceção — inclusive `KeyboardInterrupt`, `SystemExit` e bugs de programação.
**Impact:** Erros reais ficam invisíveis no log; comportamento indefinido silencioso em caso de falha inesperada.
**Recommendation:** Capturar exceções específicas (`except SQLAlchemyError`, `except ValueError`); logar antes de retornar a mensagem genérica.

### [MEDIUM] Deprecated `datetime.utcnow()` (OBS-01)
**File:** `models/task.py:16-17`, `models/user.py:14`, `routes/task_routes.py:31,73,215,285`, `routes/report_routes.py:35,46,50,133`
**Description:** `datetime.utcnow()` foi deprecated no Python 3.12; chamadas diretas e defaults de coluna usam esta API em pelo menos 8 locais.
**Impact:** Emite `DeprecationWarning` em Python 3.12+; em Python 3.14 a remoção está prevista, quebrando o código.
**Recommendation:** Substituir por `datetime.now(timezone.utc)` e importar `timezone` de `datetime`.

### [MEDIUM] Deprecated `default=datetime.utcnow` in `db.Column` (OBS-02)
**File:** `models/user.py:14`, `models/task.py:16-17`, `models/category.py:9`
**Description:** `db.Column(db.DateTime, default=datetime.utcnow)` passa a referência de função deprecated; o mesmo problema se repete em `onupdate=datetime.utcnow` (`models/task.py:17`).
**Impact:** Mesmo impacto de OBS-01 ampliado para colunas com default automático de timestamp.
**Recommendation:** `default=lambda: datetime.now(timezone.utc)` e `onupdate=lambda: datetime.now(timezone.utc)`.

### [LOW] Magic Strings / Numbers
**File:** `routes/task_routes.py:110`, `routes/report_routes.py:24-28`, `routes/user_routes.py:71`
**Description:** Literais como `'pending'`, `'in_progress'`, `'done'`, `'cancelled'` e `'user'`, `'admin'`, `'manager'` espalhados por múltiplos arquivos. `report_routes.py:24-28` usa `p1`/`p2`/`p3`/`p4`/`p5` para contar por prioridade.
**Impact:** Renomear um status exige busca manual em todos os arquivos; `p1` a `p5` não comunicam que representam prioridades.
**Recommendation:** Usar as constantes já definidas em `utils/helpers.py` (`VALID_STATUSES`, `VALID_ROLES`) nas rotas; substituir `p1-p5` por nomes descritivos como `priority_critical`.

### [LOW] Poor Variable Naming
**File:** `routes/report_routes.py:24-28`, `routes/task_routes.py:18`, `routes/user_routes.py:14`
**Description:** Variáveis `p1`/`p2`/`p3`/`p4`/`p5` em escopo de função, `t` em loops de 50+ linhas, `u` em loops de lista — nomes de 1-2 caracteres em escopos grandes.
**Impact:** Leitura comprometida; mantenedor precisa rastrear manualmente o significado de cada variável.
**Recommendation:** Nomes descritivos: `priority_1_count`, `task`, `user`.

### [LOW] Log via `print()`
**File:** `routes/task_routes.py:149,153,219,234`, `routes/user_routes.py:83,89`
**Description:** Eventos como criação, atualização e erros são logados via `print()` sem nível de severidade ou formato estruturado.
**Impact:** Impossível filtrar por nível em produção; sem timestamp nem contexto estruturado para rastreabilidade.
**Recommendation:** Substituir por `logging.getLogger(__name__)` com nível adequado (`logger.info`, `logger.error`).

### [LOW] Type Check via `type()` Instead of `isinstance()`
**File:** `routes/task_routes.py:141`, `routes/task_routes.py:212`, `utils/helpers.py:103`
**Description:** `if type(tags) == list:` falha para subclasses de `list` e é considerado anti-Pythônico.
**Impact:** Comportamento incorreto com subclasses; estilo não-idiomático.
**Recommendation:** `if isinstance(tags, list):`.

================================
Total: 20 findings
================================
