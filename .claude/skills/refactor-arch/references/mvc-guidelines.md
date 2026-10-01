# Guidelines de Arquitetura — Estrutura MVC Alvo

As regras abaixo valem **independente da linguagem** — só o nome dos arquivos/imports
muda entre stacks.

## Fluxo de uma requisição (visão geral antes do detalhe por camada)

```
HTTP request
  → views/routes: extrai body/params, valida contra schema
  → controllers: orquestra o caso de uso, chama o(s) model(s)
  → models: persistência — query sempre parametrizada
  → controllers: monta o payload de retorno (lógico, não serializado)
  → views/routes: serializa a resposta em JSON
  → response

Erro em qualquer camada → middlewares/error_handler → resposta HTTP padronizada
```

Cada camada só conhece a camada abaixo dela: **Route → Controller → Model → DB**, nunca
o inverso. O entry point (`app.py`/`app.js`) é o único lugar que "conhece" a aplicação
inteira — ele só monta as peças, não executa lógica.

## Estrutura de pastas — Python/Flask

```
src/
├── app.py                   # Composition root: cria app, registra blueprints, carrega middlewares
├── config/
│   ├── __init__.py
│   └── settings.py          # Lê env vars, expõe config (SECRET_KEY, DB_URL, DEBUG)
├── models/                  # Acesso a dados + entidades
│   ├── __init__.py
│   ├── <entidade>_model.py  # Ex: produto_model.py, usuario_model.py
│   └── database.py          # Factory de conexão / Session / init_db
├── controllers/             # Orquestração de fluxo (caso de uso)
│   ├── __init__.py
│   └── <entidade>_controller.py
├── views/                   # Roteamento (blueprints/routers) — "views" em API = rotas
│   ├── __init__.py
│   └── <entidade>_routes.py
├── middlewares/
│   ├── __init__.py
│   ├── error_handler.py     # Captura exceções e retorna response padrão
│   └── auth.py              # Guard global deny-by-default + require_role (se houver rotas protegidas)
├── schemas/                 # Validação de payload (opcional, Marshmallow/Pydantic)
│   └── <entidade>_schema.py
└── utils/                   # Helpers puros — sem side effects
    └── security.py          # hash, token, etc.
```

## Estrutura de pastas — Node.js/Express

```
src/
├── app.js                   # Composition root
├── server.js                # (opcional) listen() separado do app para facilitar testes
├── config/
│   └── index.js             # Lê process.env e expõe config
├── models/
│   ├── <entidade>.model.js
│   └── db.js                # Conexão/pool
├── controllers/
│   └── <entidade>.controller.js
├── routes/                  # "views" em Express
│   ├── index.js
│   └── <entidade>.routes.js
├── middlewares/
│   ├── errorHandler.js
│   ├── auth.js              # requireAuth/requireAdmin — montado no router, fail-closed
│   └── validate.js
└── utils/
    ├── crypto.js
    └── logger.js
```

O nome exato das pastas pode variar entre projetos (`controllers/` ↔ `services/`,
`views/` ↔ `routes/`) — o que não pode variar é a separação de responsabilidade que a
tabela abaixo descreve.

## Responsabilidade por camada

| Camada | Responsável por | Fora de escopo (não deve fazer) |
|---|---|---|
| `config/` | Ler `os.environ`/`process.env`, aplicar defaults seguros, expor config imutável. **Zero** string sensível literal — `SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-never-use-in-prod")`. | Lógica de negócio, side effects, print/log. |
| `models/` | Definir schema (tabela/coluna/constraint); encapsular queries sempre **parametrizadas**; expor acesso a dado (`find_by_id`, `save`, `delete`); método de domínio da própria entidade (`is_overdue`, `total`). | Tocar `request`/`response`; validar payload de usuário; formatar para JSON/HTML. |
| `controllers/` | Receber dado já parseado/validado; chamar model(s)/service(s) na ordem certa; decidir **o quê** responder; lançar exceção tipada (`NotFoundError`, `ValidationError`) para o middleware tratar; aplicar a autorização de negócio (dono do recurso, quem pode gravar campos de privilégio) com o `current_user` recebido da view. | Query SQL crua; acessar variável global mutável; serializar para JSON (isso é da view). |
| `views/`/`routes/` | Declarar rota + método HTTP; extrair `params`/`body`/`query`; acionar validação de schema; chamar o controller certo; serializar a resposta (DTO). | Acessar o banco diretamente; qualquer cálculo além de montar a resposta. |
| `middlewares/` | Error handler central (`Error` → status HTTP + JSON); autenticação/autorização; parsing, rate limit, CORS; log de request. | Lógica de negócio. |
| `utils/` | Função pura sem dependência de framework (hash, UUID, formatação de data). | Qualquer I/O, estado global, dependência pesada. |

## Checklist arquitetural (rode ao final da Fase 3)

- [ ] `app.py`/`app.js` tem menos de 50 linhas e só monta a aplicação.
- [ ] Nenhum arquivo fora de `config/` contém segredo literal.
- [ ] Não sobrou nenhum `cursor.execute("..." + var)`.
- [ ] Nenhum model importa `request`/`req`.
- [ ] Nenhuma view/route tem query SQL direta.
- [ ] Erros passam por um middleware central — não por `try/except` em cada handler.
- [ ] Existe uma factory/init clara de banco, não uma conexão global mutável.
- [ ] Há pelo menos 1 arquivo por domínio em cada camada (models, controllers, routes).
- [ ] Senha usa hash forte (bcrypt/argon2) — nunca MD5/SHA1/texto plano.
- [ ] Autenticação é aplicada no nível do app/router (deny-by-default), com allowlist explícita de rotas públicas — não só por decorator em cada rota.
- [ ] Nenhum guard libera acesso quando o segredo está vazio; segredos de acesso são obrigatórios no boot (sem default literal, sem `''`).
- [ ] Todo token emitido pelo login é verificado por um middleware ativo; operações de privilégio exigem papel `admin`.
- [ ] Campos de privilégio (`role`, `active`...) só são graváveis por `admin` em qualquer rota — inclusive no update genérico de usuário.
- [ ] Nenhum controller usa id de dono vindo do payload; rotas com id de usuário servem só o próprio usuário ou um admin (checagem no controller com o `current_user` do token).

## Armadilhas a evitar

- Criar um `utils/`/`helpers/` fila-única com 15 funções sem relação entre si.
- Adicionar `services/` além de `controllers/` sem necessidade real — em projeto
  pequeno o controller já cumpre esse papel; só separe se houver lógica reaproveitada
  entre múltiplos controllers.
- Quebrar contrato de endpoint: todo método HTTP + path original precisa continuar
  respondendo com o mesmo status code de antes.
- Criar arquivo vazio "de placeholder" que não faz nada — só atrapalha navegação.
- Sobre-engenharia: projeto de 4 endpoints não precisa de Repository + Unit of Work + container de DI.
