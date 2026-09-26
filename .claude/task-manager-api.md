# Projeto 3 — task-manager-api (Python/Flask)

API de Task Manager (tasks, usuários, categorias). Diferente dos outros dois, **já tem
separação de pastas** (`models/`, `routes/`, `services/`, `utils/`) — mas a organização
física não significa arquitetura correta: rotas continuam gordas e há falhas de
segurança sérias.

## Como rodar

```bash
cd task-manager-api
pip install -r requirements.txt
python seed.py   # popular o banco ANTES do primeiro boot
python app.py
```

Sobe em `http://localhost:5000`. SQLite (`tasks.db`).

## Estrutura atual

```
task-manager-api/
├── app.py                       # bootstrap + registro de blueprints
├── database.py                  # instância SQLAlchemy
├── seed.py                      # popula usuários, categorias e tasks
├── models/
│   ├── task.py / user.py / category.py
├── routes/
│   ├── task_routes.py    (299 linhas — validação + serialização + N+1 no handler)
│   ├── user_routes.py    (211 linhas)
│   └── report_routes.py  (223 linhas — relatórios com N+1 pesado)
├── services/
│   └── notification_service.py  # existe mas não é chamado pelas rotas
└── utils/
    └── helpers.py                # `process_task_data` duplica validação já feita nas rotas
```

## Problemas identificados (análise manual)

- **[CRITICAL] Exposição de senha (hash) na API** —
  [`models/user.py:16-25`](../task-manager-api/models/user.py#L16) (`to_dict`) inclui
  `'password': self.password` — todo endpoint que serializa um usuário (ex.:
  `GET /users`) vaza o hash da senha no JSON.
- **[CRITICAL] Hashing de senha com API/algoritmo obsoleto** —
  [`models/user.py:27-32`](../task-manager-api/models/user.py#L27): MD5 sem salt para
  `set_password`/`check_password` — deprecated para senhas, deveria usar
  `werkzeug.security.generate_password_hash` (PBKDF2) ou `bcrypt`.
- **[HIGH] Regras de negócio e validação dentro das rotas (fat routes)** —
  [`routes/task_routes.py:85-154`](../task-manager-api/routes/task_routes.py#L85)
  (`create_task`) e `update_task` (linhas 156-223) fazem validação de campo a campo,
  parsing de data e lookup de FK diretamente no handler, sem passar pela camada
  `services/` que já existe na pasta.
- **[HIGH] Validação duplicada e não usada** —
  [`utils/helpers.py:56-101`](../task-manager-api/utils/helpers.py#L56)
  (`process_task_data`) reimplementa a mesma validação de `create_task`/`update_task`
  em `task_routes.py`, mas **não é chamada de lugar nenhum** — duas fontes de verdade
  divergentes para a mesma regra.
- **[MEDIUM] N+1 queries em relatório** —
  [`routes/report_routes.py:53-56`](../task-manager-api/routes/report_routes.py#L53):
  para cada usuário, dispara uma query `Task.query.filter_by(user_id=u.id).all()`
  dentro do loop; e em
  [`routes/task_routes.py:41-57`](../task-manager-api/routes/task_routes.py#L41)
  (`get_tasks`), para cada task busca `User` e `Category` individualmente em vez de
  usar `join`/`joinedload`.
- **[MEDIUM] Credenciais SMTP hardcoded em serviço morto** —
  [`services/notification_service.py:9-12`](../task-manager-api/services/notification_service.py#L9):
  `email_user`/`email_password` fixos no código; o serviço nem é chamado pelas rotas,
  então é dead code com segredo hardcoded.
- **[MEDIUM] `SECRET_KEY` hardcoded** —
  [`app.py:13`](../task-manager-api/app.py#L13): `'super-secret-key-123'`.
- **[LOW] `except:` genérico (bare except)** —
  [`routes/task_routes.py:62`](../task-manager-api/routes/task_routes.py#L62) e
  [`utils/helpers.py:44-47`](../task-manager-api/utils/helpers.py#L44) escondem
  qualquer erro, inclusive `KeyboardInterrupt`/bugs de programação.
- **[LOW] Lógica de "overdue" duplicada em 3 lugares** —
  repetida quase idêntica em `task_routes.py:30-39`, `task_routes.py:71-80` e
  `report_routes.py:33-43`, em vez de um método único no model `Task`.
- **[LOW] Imports não usados / nomenclatura genérica** — `import json, os, sys, time`
  no topo de [`task_routes.py:7`](../task-manager-api/routes/task_routes.py#L7) sem uso
  aparente de `os`/`sys`/`time`; variáveis de uma letra (`t`, `u`, `p1`..`p5`) em loops.

## Notas para a skill

- Skill é **copiada** para cá também. Este é o teste mais importante de que a skill
  não se baseia em "está tudo em um arquivo só" — ela precisa achar problemas mesmo
  com pastas já separadas.
- Cobrir explicitamente no catálogo: "fat route/controller mesmo com camadas
  existentes", "validação duplicada/morta", "hash de senha deprecated (MD5)" e
  "serialização vazando campos sensíveis".
- Refatoração alvo aqui é mais cirúrgica que nos projetos 1 e 2: mover a lógica de
  `task_routes.py`/`report_routes.py` para dentro de `services/`, remover
  `process_task_data` duplicado (ou fazer as rotas usarem só ele), corrigir
  `to_dict()` para nunca devolver `password`, trocar MD5 por hash seguro, e
  centralizar a checagem de "overdue" no model `Task`.
- Validar Fase 3 rodando `seed.py` novamente antes de subir a app, e conferindo que
  `GET /tasks`, `GET /reports/summary` e `POST /users` (login) continuam respondendo.
