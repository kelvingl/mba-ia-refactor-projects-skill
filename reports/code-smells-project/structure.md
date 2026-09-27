# Comparação de Estrutura — code-smells-project

Registro da transformação arquitetural executada pela skill `refactor-arch`.

---

## Antes — Monolítica por arquivo (4 arquivos, raiz plana)

```
code-smells-project/
├── app.py           (89 linhas)  ← entry point + rotas embutidas + endpoints /admin/* perigosos
├── controllers.py  (292 linhas)  ← handlers HTTP com validação inline e lógica de negócio misturada
├── models.py       (314 linhas)  ← God Module: queries SQL, orquestração de pedidos, cálculo de descontos, serialização
├── database.py      (86 linhas)  ← conexão global mutável (db_connection = None), schema e seeds juntos
├── requirements.txt  (2 deps)
└── README.md
```

**Total:** 4 arquivos-fonte · 781 linhas efetivas de código

### Problemas identificados (resumo do relatório Fase 2)

| Severidade | Ocorrência |
|---|---|
| CRITICAL | SQL injection via concatenação em 12+ queries |
| CRITICAL | `SECRET_KEY` hardcoded em `app.py:7`, exposto em `/health` |
| CRITICAL | Senhas em texto plano — sem hash no insert/login |
| CRITICAL | `/admin/query` aceita SQL arbitrário sem autenticação |
| CRITICAL | `DEBUG = True` sem condicional de ambiente |
| CRITICAL | `models.py` com 314 linhas sem nenhuma separação de camadas |
| HIGH | `db_connection = None` global mutável em `database.py:4` |
| HIGH | N+1 queries: 3 cursores aninhados em loops de pedidos |
| HIGH | `try/except Exception` repetido em cada handler (11 blocos) |
| MEDIUM | Validação de produto duplicada em `criar_produto` e `atualizar_produto` |
| LOW | Thresholds de desconto hardcoded (10000, 5000, 1000) em `models.py:256` |

---

## Depois — MVC em `src/` (13 arquivos, 6 camadas)

```
code-smells-project/
├── app.py             (10 linhas)  ← entry point mínimo (importa create_app e chama run)
├── requirements.txt    (3 deps)
├── README.md
└── src/
    ├── app.py          (47 linhas)  ← composition root: cria app, registra blueprints e middlewares
    │
    ├── config/
    │   └── settings.py  (8 linhas)  ← lê SECRET_KEY, FLASK_DEBUG, DATABASE_PATH de variáveis de ambiente
    │
    ├── models/
    │   ├── database.py      (96 linhas)  ← factory com Flask.g (per-request), init_db, teardown
    │   ├── produto_model.py  (79 linhas)  ← CRUD com prepared statements + busca dinâmica segura
    │   ├── usuario_model.py  (47 linhas)  ← sem retornar senha; login via verify_password
    │   └── pedido_model.py  (117 linhas)  ← 2 JOINs substituem N+1 (cursor2/cursor3 em loop)
    │
    ├── controllers/
    │   ├── produto_controller.py    (52 linhas)  ← validação centralizada + chama model
    │   ├── usuario_controller.py    (28 linhas)  ← login/create sem senha em texto plano
    │   ├── pedido_controller.py     (37 linhas)  ← orquestração com exceções tipadas
    │   └── relatorio_controller.py  (45 linhas)  ← desconto em DISCOUNT_TIERS constante
    │
    ├── views/
    │   └── routes.py  (149 linhas)  ← blueprints Flask, sem SQL, sem lógica de negócio
    │
    ├── middlewares/
    │   └── error_handler.py  (31 linhas)  ← AppError, NotFoundError, ValidationError + handlers registrados
    │
    └── utils/
        └── security.py  (7 linhas)  ← hash_password / verify_password via werkzeug
```

**Total:** 13 arquivos-fonte · 743 linhas distribuídas em 6 camadas

---

## Diferenças lado a lado

| Aspecto | Antes | Depois |
|---|---|---|
| Arquivos-fonte | 4 | 13 |
| Pastas | 0 (raiz plana) | 6 camadas (`config`, `models`, `controllers`, `views`, `middlewares`, `utils`) |
| Linhas totais | 781 | 743 |
| Maior arquivo | `models.py` — 314 linhas | `src/views/routes.py` — 149 linhas |
| Entry point (`app.py`) | 89 linhas (rotas + lógica + seeds) | 10 linhas (só `create_app` + `run`) |
| SQL Injection | 12+ pontos de concatenação | 0 — prepared statements em todos os modelos |
| Segredos no código | `SECRET_KEY` literal em `app.py:7` | Lidos de `os.environ` em `src/config/settings.py` |
| Hash de senha | Texto plano no banco | `werkzeug.security.generate_password_hash` |
| Endpoint `/admin/query` | Existia sem autenticação | Removido |
| Debug mode | `True` hardcoded | Controlado por `FLASK_DEBUG` env var |
| Conexão de banco | Global mutável (`db_connection = None`) | `Flask.g` per-request via `get_db()` |
| N+1 queries em pedidos | 2–3 cursores aninhados por pedido | 1 JOIN com agrupamento em dicionário |
| Error handling | 11 blocos `try/except Exception` dispersos | 1 middleware central (`src/middlewares/error_handler.py`) |
| Senha na resposta JSON | Retornada em `/usuarios` e `/usuarios/:id` | Nunca retornada (campos excluídos no model) |

---

## Fluxo de request antes e depois

**Antes:**
```
HTTP request → app.py (rota) → controllers.py (validação + lógica) → models.py (query concatenada + negócio) → resposta
```

**Depois:**
```
HTTP request → src/views/routes.py (extrai params) → src/controllers/ (orquestra)
             → src/models/ (query parametrizada) → src/controllers/ (monta payload)
             → src/views/routes.py (serializa JSON) → resposta

Erro em qualquer camada → src/middlewares/error_handler.py → JSON padronizado
```
