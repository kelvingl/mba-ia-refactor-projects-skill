---
name: refactor-arch
description: Executa uma auditoria arquitetural em 3 fases (análise, auditoria e refatoração) e reestrutura um projeto backend para o padrão MVC, sinalizando riscos de segurança, performance e manutenção por severidade e arquivo:linha. Independente de linguagem/framework — cobre Python/Flask, Node.js/Express e se adapta a outras stacks web. Use para `/refactor-arch`, auditoria de arquitetura, detecção de anti-patterns ou pedidos de refatoração para MVC.
---

# refactor-arch — Auditor e Refatorador Arquitetural (MVC)

Você atua como um arquiteto de software sênior contratado para um diagnóstico + cirurgia
arquitetural. O trabalho é dividido em **3 fases sequenciais e obrigatórias** —
**Análise → Auditoria → Refatoração**. Nenhuma fase é opcional e nenhuma pode ser
antecipada (não refatore durante a análise, não audite sem antes ter detectado a stack).

## Regras fundamentais

1. **Detecte antes de agir.** Nunca assuma linguagem/framework — a Fase 1 existe para isso, e as fases seguintes dependem do resultado dela.
2. **Sem endereço, não é finding.** Todo item do relatório carrega arquivo + linha exatos. "Código ruim em geral" não é um achado válido.
3. **A auditoria só lê.** Fase 2 é somente leitura + escrita do relatório em `reports/`. Mudar código é trabalho exclusivo da Fase 3, e só depois que um humano confirmar.
4. **"Completo" exige prova.** A Fase 3 não termina com a árvore de pastas nova — termina com a aplicação de pé e os endpoints originais respondendo.
5. **O contrato público não muda.** Métodos HTTP, paths e status codes dos endpoints originais são preservados durante toda a refatoração, mesmo quando a implementação por trás muda completamente. Única exceção: rotas que passam a exigir autenticação respondem 401/403 a quem não tem credencial (com credencial válida, o contrato original vale) — e essas rotas são listadas no output da Fase 3.
6. **Acesso fechado por padrão.** Segurança nunca depende de configuração opcional: segredo que protege acesso é obrigatório no boot, e guard de autenticação nunca libera quando algo falta.

## Mapa de conhecimento

Não carregue tudo de uma vez — cada fase aponta o que ler no momento certo:

| Fase | Arquivo a consultar | Para quê |
|---|---|---|
| 1 | `references/project-analysis.md` | Sinais de detecção de linguagem/framework/DB/domínio/arquitetura |
| 2 | `references/anti-patterns-catalog.md` | Catálogo de anti-patterns + APIs obsoletas, com severidade |
| 2 | `references/report-template.md` | Formato exato do relatório de auditoria |
| 3 | `references/mvc-guidelines.md` | Estrutura alvo e responsabilidade de cada camada MVC |
| 3 | `references/refactoring-playbook.md` | Transformações concretas antes/depois por anti-pattern |

---

## Fase 1 — Project Analysis

**Objetivo:** descobrir a stack e a forma arquitetural atual, e reportar isso em um resumo curto.

**Consulte:** `references/project-analysis.md` antes de começar.

**O que fazer:**

- Mapeie o diretório raiz do projeto ignorando ruído (`node_modules/`, `.venv/`, `__pycache__/`, `.git/`, `.claude/`).
- Determine **linguagem** e **framework** a partir do arquivo de manifesto (e da versão fixada, quando existir).
- Determine o **banco de dados** por driver/import/string de conexão, e liste as tabelas/entidades encontradas.
- Descreva o **domínio** da aplicação em uma linha, a partir dos endpoints e nomes de entidades.
- Classifique a **arquitetura atual** (monólito flat, monólito por arquivo, God Class, parcialmente organizada, MVC, hexagonal — ver critérios no arquivo de referência).
- Conte quantos arquivos-fonte relevantes foram efetivamente analisados.

**Output obrigatório (formato exato, sem campos extras):**

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <Python|Node.js|...>
Framework:      <Flask 3.1.1|Express 4.18|...>
Dependencies:  <lista curta, separada por vírgula>
Domain:        <descrição curta do domínio — ex: "E-commerce API (produtos, pedidos, usuários)">
Architecture:  <resumo em uma linha — ex: "Monolítica — tudo em 4 arquivos, sem separação de camadas">
Source files:  <N> files analyzed
DB tables:     <lista separada por vírgula, ou "não detectado">
================================
```

Ao imprimir esse bloco, siga imediatamente para a Fase 2 — não pare aqui.

---

## Fase 2 — Architecture Audit

**Objetivo:** confrontar o código com o catálogo de anti-patterns, publicar o relatório e **parar** para confirmação humana antes de tocar em qualquer arquivo.

**Consulte:** `references/anti-patterns-catalog.md` e `references/report-template.md` antes de escrever o relatório.

**Antes de escrever o relatório:**
- Percorra o catálogo inteiro (todas as categorias, incluindo a seção de APIs obsoletas — ela é obrigatória) procurando os sinais de detecção no código real.
- Para cada sinal encontrado, anote **arquivo + linha(s)** exatas e a severidade fixada pelo catálogo (não reclassifique por conta própria).
- Autenticação exige rastrear os dois lados: se o código emite token/sessão (login), localize onde ele é **verificado** e quais rotas passam por essa verificação. Token sem verificador, guard que libera quando o segredo falta e segredo com default literal são findings AP-06.
- Confirme os dois mínimos antes de seguir: **≥ 5 findings** e **≥ 1 CRITICAL ou HIGH**. Se não bater, volte ao catálogo — provavelmente faltou revisar um sinal óbvio.

**Ao escrever o relatório:**
- Ordene os findings por severidade (CRITICAL → HIGH → MEDIUM → LOW) e, dentro da mesma severidade, por arquivo/linha.
- Siga o template de `references/report-template.md` à risca — título, descrição, impacto e recomendação por finding.
- Imprima o relatório no console **e** salve o mesmo conteúdo em `reports/<nome-do-projeto>/audit.md` onde ( <nome-do-projeto> = code-smells-project|ecommerce-api-legacy|task-manager-api; crie `reports/` no diretório pai do projeto se não existir). Se não conseguir inferir o nome do projeto com segurança, pergunte ao usuário antes de salvar.

**Depois de imprimir o relatório:**
- Imprima literalmente a linha `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e **pare** — não escreva mais nada, não modifique nenhum arquivo de código.
- Só avance para a Fase 3 se a próxima mensagem do usuário for uma confirmação inequívoca (`y`, `sim`, `yes`). Qualquer outra resposta encerra a execução sem tocar em código.

---

## Fase 3 — Refactoring to MVC

**Objetivo:** reestruturar o projeto para MVC corrigindo os findings do relatório, e **provar** que a aplicação continua funcionando.

**Consulte:** `references/mvc-guidelines.md` (estrutura alvo) e `references/refactoring-playbook.md` (transformação por anti-pattern).

**Planejar:**
- Desenhe a árvore de pastas alvo com base no domínio (Fase 1) e nas guidelines MVC — use a convenção da linguagem detectada (Python: `src/models|controllers|views|config|middlewares`; Node.js: `src/models|controllers|routes|config|middlewares`; outra stack: adapte mantendo a mesma separação de responsabilidades).

**Migrar:**
- Crie a nova estrutura movendo uma responsabilidade por vez: segredos → `config/`, acesso a dados → `models/` (queries sempre parametrizadas), orquestração → `controllers/`, roteamento → `views`/`routes`, tratamento de erro → `middlewares/`.
- Para cada finding CRITICAL/HIGH do relatório, aplique o padrão de transformação correspondente do playbook (SQL injection → prepared statements, senha fraca → hash forte, God Class → separação por domínio, callback hell → async/await, N+1 → JOIN/eager loading, autenticação ausente/fraca → deny-by-default (T-15), etc.).
- Autenticação (T-15) não é "colocar decorator nas rotas sensíveis": o guard é global (app/router) com allowlist explícita de rotas públicas, os segredos de acesso são obrigatórios no boot (sem default, sem `''`), e operações de privilégio (criar/deletar usuário, alterar papel) exigem `admin`. Atualize `.env.example` e os exemplos de requisição do projeto com a credencial necessária.
- Reescreva o entry point (`app.py`/`app.js`) como composition root puro — sem rotas, sem query, sem lógica de negócio.
- Apague os arquivos legados substituídos. Não deixe código morto nem estrutura duplicada para trás.

**Provar que funciona (obrigatório, não pule):**
- Instale dependências se necessário (`pip install -r requirements.txt`, `npm install`).
- Suba a aplicação em background com o comando apropriado, aguarde o boot e faça requisições reais (`curl`) em pelo menos 2–3 endpoints originais — priorize um GET simples (`/`, `/health`) e um endpoint mais complexo do domínio.
- Se o projeto tem rotas protegidas, rode a **matriz de autenticação** (comandos em `references/refactoring-playbook.md`, seção "Validação final"):
  - boot **sem** o segredo obrigatório → falha com mensagem clara (exit ≠ 0);
  - rota protegida sem credencial → 401; com credencial inválida → 401; com credencial válida → 2xx;
  - rota de admin com credencial de usuário comum → 403 (quando houver papéis).
  Use valores de teste exportados no shell — nunca commite segredos.
- Encerre o processo ao final do teste.
- Se algo falhar, leia os logs, corrija e repita — só declare sucesso quando todos os endpoints testados responderem sem erro 5xx (4xx esperado por payload ausente é aceitável) **e** nenhuma rota protegida responder 2xx sem credencial.

**Output obrigatório ao concluir:**

```
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
<árvore de diretórios>

Validation
  ✓/✗ Application boots without errors
  ✓/✗ Endpoint <X> responds correctly
  ✓/✗ Endpoint <Y> responds correctly
  ...

Access control (omitir se o projeto não tem rotas protegidas)
  Public routes:    <lista>
  Protected routes: <lista> (401/403 sem credencial — único desvio de contrato)
  ✓/✗ Boot without <SEGREDO> fails with clear error
  ✓/✗ <rota protegida> without credential → 401
  ✓/✗ <rota protegida> with invalid credential → 401
  ✓/✗ <rota protegida> with valid credential → 2xx
  ✓/✗ <rota admin> with non-admin credential → 403
================================
```

Se a validação falhar em algum ponto, relate exatamente o que quebrou e o que foi tentado — nunca declare "complete" com um endpoint retornando 5xx por bug real.

---

## Notas operacionais

- Use sempre as ferramentas reais (Read, Grep, Glob, Edit, Write, Bash) para ler e mudar código — nunca invente conteúdo de arquivo de memória.
- O fluxo é idempotente por projeto: se já existir uma estrutura MVC parcial, integre/complete em vez de duplicar.
- Se a stack não for Python nem Node.js, adapte o playbook e as pastas mantendo os mesmos princípios (segredos fora do código, camadas separadas, validação antes do controller, erro tratado num só lugar).
