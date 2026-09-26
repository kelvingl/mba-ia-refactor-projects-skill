# Projeto 1 — code-smells-project (Python/Flask)

API de E-commerce (produtos, usuários, pedidos). Monólito **desestruturado**: 4 arquivos,
zero separação de camadas, ~800 linhas.

## Como rodar

```bash
cd code-smells-project
pip install -r requirements.txt
python app.py
```

Sobe em `http://localhost:5000`. SQLite (`loja.db`) criado automaticamente no boot,
já populado com produtos/usuários de exemplo.

## Estrutura atual

```
code-smells-project/
├── app.py          # Flask app + registro de rotas + 2 endpoints de admin embutidos
├── controllers.py  # "controllers" que já fazem validação, acesso a dados e formatação
├── models.py       # queries SQL cruas, sem ORM
└── database.py     # conexão global + criação de schema + seed
```

Tabelas: `produtos`, `usuarios`, `pedidos`, `itens_pedido`.

## Problemas identificados (análise manual)

- **[CRITICAL] Hardcoded credentials** — [`app.py:7`](../code-smells-project/app.py#L7):
  `SECRET_KEY = "minha-chave-super-secreta-123"` direto no código.
- **[CRITICAL] SQL Injection** — [`app.py:59-78`](../code-smells-project/app.py#L59):
  endpoint `/admin/query` executa SQL arbitrário vindo do body da requisição, sem
  nenhuma validação; e [`models.py:26`](../code-smells-project/models.py#L26)
  (`get_produto_por_id`) concatena `id` direto na query com `+ str(id)`.
- **[CRITICAL] God Class / falta de separação MVC** — `models.py` (314 linhas) reúne
  queries SQL cruas de 4 domínios diferentes (produtos, usuários, pedidos, itens);
  `app.py` mistura composition root, rotas e regras de negócio de admin no mesmo arquivo.
- **[HIGH] Senhas em texto plano** — [`database.py:64-71`](../code-smells-project/database.py#L64)
  grava senhas de seed sem hash (`"admin123"`, `"123456"`); não há hashing em nenhum
  fluxo de criação/login de usuário em `controllers.py`.
- **[HIGH] Endpoint de reset de banco sem autenticação** —
  [`app.py:47-57`](../code-smells-project/app.py#L47) (`/admin/reset-db`) apaga todas
  as tabelas via POST sem qualquer controle de acesso.
- **[MEDIUM] Falta de validação/normalização consistente** — cada função em
  `controllers.py` reimplementa validação manual de campos obrigatórios (ex.:
  `criar_produto`, linhas ~26-40) sem um padrão único ou camada de schema.
- **[MEDIUM] Ausência de tratamento de exceção específico** — `try/except Exception`
  genérico espalhado por `controllers.py`, sempre devolvendo `str(e)` cru no JSON de
  erro (vaza detalhes internos ao cliente).
- **[LOW] Concatenação de string em vez de f-string/logging** —
  [`controllers.py:7`](../code-smells-project/controllers.py#L7):
  `print("Listando " + str(len(produtos)) + " produtos")`.
- **[LOW] `DEBUG = True` fixo em produção** — [`app.py:8`](../code-smells-project/app.py#L8)
  e `app.run(..., debug=True)` em `app.py:88`.
- **[LOW] Repetição de dicionário de serialização** — `models.py` monta o mesmo dict de
  produto manualmente em pelo menos duas funções (`get_todos_produtos`,
  `get_produto_por_id`) em vez de um único serializer.

## Notas para a skill

- É o projeto onde a skill `refactor-arch` deve ser **criada primeiro**
  (`.claude/skills/refactor-arch/`), servindo de baseline antes de copiar para os
  outros dois.
- Bom caso de teste para "God Class" e SQL Injection — cobrir esses dois padrões no
  catálogo de anti-patterns é obrigatório aqui.
- Refatoração alvo: separar em `models/` (por domínio: produto, usuario, pedido),
  `controllers/` finos, `views/routes.py`, `config/settings.py` (sem hardcode) e
  `middlewares/error_handler.py`.
