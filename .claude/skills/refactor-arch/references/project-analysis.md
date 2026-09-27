# Sinais de Detecção — Fase 1

Cada passo abaixo depende do resultado do anterior — siga a sequência, não pule para o
domínio antes de confirmar linguagem e framework.

## Passo 1 — Linguagem

Olhe primeiro o **arquivo de manifesto** na raiz do projeto:

| Manifesto encontrado | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile` | Python |
| `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock` | Node.js (JS/TS) |
| `pom.xml`, `build.gradle`, `build.gradle.kts` | Java / Kotlin |
| `Gemfile`, `.ruby-version` | Ruby |
| `go.mod` | Go |
| `composer.json` | PHP |
| `Cargo.toml` | Rust |

Sem manifesto: use a extensão dominante entre os arquivos-fonte (`.py`, `.js`, `.ts`,
`.rb`, `.java`...). Versão do runtime (`"engines"` no `package.json`, `python_requires`
no `setup.py`) é bônus, não obrigatória no output.

## Passo 2 — Framework

Com a linguagem definida, abra o manifesto e procure a dependência que a identifica:

**Python:** `flask` → Flask · `django` → Django · `fastapi` → FastAPI · `starlette` →
Starlette · `tornado` → Tornado · `bottle` → Bottle · `aiohttp` → aiohttp

**Node.js:** `express` → Express · `koa` → Koa · `fastify` → Fastify · `@nestjs/core` →
NestJS · `hapi`/`@hapi/hapi` → Hapi · `next` → Next.js

**Outras stacks:** `spring-boot-starter-*` → Spring Boot · `rails` (Gemfile) → Ruby on
Rails · `sinatra` (Gemfile) → Sinatra · `laravel/framework` → Laravel ·
`gin-gonic/gin` (go.mod) → Gin

Reporte framework + versão quando ela estiver fixada exatamente; com caret/tilde
(`^4.18.0`), reporte como versão mínima (`Express ^4.18`).

## Passo 3 — Banco de dados

Cruze duas fontes:

1. **Driver no manifesto** — `sqlite3` → SQLite · `psycopg2`/`psycopg`/`pg` →
   PostgreSQL · `mysql`/`mysql2`/`pymysql` → MySQL · `pymongo`/`mongoose`/`mongodb` →
   MongoDB · `redis`/`ioredis` → Redis (normalmente cache) · `sqlalchemy`/
   `flask-sqlalchemy` → SQL via SQLAlchemy (olhe a URL) · `sequelize`/`typeorm`/
   `prisma` → SQL via ORM (olhe a config).
2. **Sinal no código** — string de conexão (`sqlite:///`, `postgres://`,
   `mongodb://`, `mysql://`); import de driver (`import sqlite3`,
   `require('sqlite3')`); criação de schema (`CREATE TABLE`, `db.Column`, `db.Model`,
   `@Entity`, `mongoose.Schema`).

Extraia os nomes das tabelas/coleções (de `CREATE TABLE`, `__tablename__`, `db.Model`
ou equivalente) para listar no output.

## Passo 4 — Domínio da aplicação

Leia 1–2 arquivos centrais (`app.py`, `app.js`, `main.py`, ou o maior arquivo de rotas)
e extraia: nomes de endpoint registrados, nomes de tabela/entidade, e a mensagem de
boas-vindas do `/` ou do README (se existir, geralmente resume o domínio em uma linha).

Combine 3–4 substantivos principais numa descrição curta:
- `/produtos`, `/usuarios`, `/pedidos` → **"E-commerce API (produtos, pedidos, usuários)"**
- `/checkout`, `/courses`, `/enrollments` → **"LMS API com fluxo de checkout (cursos, matrículas, pagamentos)"**
- `/tasks`, `/users`, `/categories`, `/reports` → **"Task Manager API (tarefas, usuários, categorias, relatórios)"**

## Passo 5 — Forma arquitetural atual

Classifique pelo sinal mais forte encontrado, começando pela forma mais desorganizada:

| Forma | Como reconhecer |
|---|---|
| Monolítica flat | Tudo em 1 arquivo (rotas + DB + lógica no mesmo lugar) |
| Monolítica por arquivo | Poucos arquivos na raiz (`app.py`, `models.py`, `controllers.py`), sem subpastas |
| God Class / God Manager | Uma classe grande (200+ linhas) concentra tudo (`AppManager`, `Service`, `Utils`) |
| Parcialmente organizada | Pastas `models/`, `routes/`, `services/` existem, mas com responsabilidades misturadas (rota validando, model com lógica de negócio) |
| MVC adequada | Camadas claras, cada uma isolada na sua responsabilidade |
| Hexagonal / Clean | `domain/`, `application/`, `infrastructure/` |

**Contagem de arquivos-fonte:** conte só extensões da linguagem primária, excluindo
`node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `.git/`, `.claude/`, migrações
auto-geradas e (se muito numerosos) arquivos de teste triviais — nesse caso reporte à
parte como "+N test files".

## Casos ambíguos

- **Múltiplos frameworks no manifesto:** reporte o que efetivamente tem endpoints registrados em uso.
- **Zero endpoints encontrados:** reporte como "biblioteca/CLI, não API web" e prossiga — o playbook MVC ainda se aplica, adaptado.
- **Sem manifesto algum:** reporte "stack inferida do código" e justifique a inferência.

## Campos do output da Fase 1

Ao final, você deve ter exatamente estes campos preenchidos (nenhum a mais):
`Language`, `Framework` (com versão quando possível), `Dependencies` (3–5 mais
relevantes além do framework), `Domain` (uma linha), `Architecture` (uma linha),
`Source files` (inteiro), `DB tables` (lista ou "não detectado").
