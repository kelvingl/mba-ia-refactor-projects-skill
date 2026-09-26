# mba-ia-refactor-projects-skill — Guia para o agente

Este repositório é a entrega do desafio **"Criação de Skills — Refatoração Arquitetural
Automatizada"**. O enunciado completo está em [`ENUNCIADO.md`](../ENUNCIADO.md) — leia
este arquivo primeiro para o essencial e vá ao enunciado quando precisar de detalhe.

## O que precisa existir no final

1. Uma skill `refactor-arch` (nome e arquivo `SKILL.md` são fixos, não renomear),
   copiada dentro de cada um dos 3 projetos em `<projeto>/.claude/skills/refactor-arch/`.
2. Os 3 projetos **refatorados para MVC** e commitados no repositório.
3. 3 relatórios de auditoria (saída da Fase 2 da skill) em `reports/audit-project-{1,2,3}.md`
   na raiz do repo.
4. `README.md` da raiz atualizado com as seções: Análise Manual, Construção da Skill,
   Resultados, Como Executar (ver enunciado, seção "README.md deve conter").

## Os 3 projetos-alvo

| # | Pasta | Stack | Organização atual | Doc detalhado |
|---|-------|-------|--------------------|----------------|
| 1 | `code-smells-project/` | Python/Flask | Monólito, 4 arquivos, zero separação de camadas | [code-smells-project.md](code-smells-project.md) |
| 2 | `ecommerce-api-legacy/` | Node.js/Express | Monólito, God Class (`AppManager`), callback hell | [ecommerce-api-legacy.md](ecommerce-api-legacy.md) |
| 3 | `task-manager-api/` | Python/Flask | Já tem `models/`, `routes/`, `services/`, `utils/`, mas com rotas gordas e falhas de segurança | [task-manager-api.md](task-manager-api.md) |

A skill precisa ser **agnóstica de tecnologia**: mesma `SKILL.md` + arquivos de
referência devem funcionar nos 3, só copiando a pasta.

## A skill `refactor-arch` — 3 fases obrigatórias

- **Fase 1 (Análise):** detecta linguagem/framework/DB, mapeia arquitetura atual, imprime resumo.
- **Fase 2 (Auditoria):** cruza o código com um catálogo de anti-patterns (mín. 8, com
  severidades distribuídas CRITICAL/HIGH/MEDIUM/LOW, incluindo detecção de APIs
  deprecated), gera relatório com arquivo+linha exatos, **pausa e pede confirmação**
  antes de mudar qualquer arquivo.
- **Fase 3 (Refatoração):** reestrutura para MVC (models/views-routes/controllers,
  config sem hardcode, error handling centralizado, entry point claro) usando um
  playbook de transformação (mín. 8 padrões antes/depois) e **valida** que a aplicação
  sobe e os endpoints originais continuam respondendo.

Arquivos de referência da skill devem cobrir 5 áreas: heurísticas de análise, catálogo
de anti-patterns, template de relatório, guidelines de arquitetura MVC e playbook de
refatoração. Organização interna dos arquivos é livre.

## Escala de severidade (usar em toda auditoria)

- **CRITICAL** — segurança grave ou "God Class" completo (DB + lógica + rotas juntos).
- **HIGH** — lógica de negócio pesada em controllers/rotas, acoplamento forte sem DI, estado global mutável.
- **MEDIUM** — N+1 queries, duplicação, middlewares mal usados, validação ausente.
- **LOW** — nomenclatura ruim, magic numbers, legibilidade.

## Critérios de aceite (obrigatórios nos 3 projetos, sem exceção)

- Fase 1 detecta a stack corretamente.
- Fase 2 encontra >= 5 findings, com pelo menos 1 CRITICAL ou HIGH.
- Fase 3 entrega aplicação funcional (boot sem erro + endpoints originais respondendo).

## Convenções de trabalho neste repo

- Não alterar o nome da skill (`refactor-arch`) nem o arquivo `SKILL.md`.
- Reports vão em `reports/audit-project-{1,2,3}.md` na raiz — não dentro dos projetos.
- Cada projeto refatorado é commitado no repositório (Fase 3 não é só local).
- Antes de aplicar a Fase 3 em qualquer projeto, o relatório da Fase 2 deve ser
  mostrado e confirmado — nunca pular essa pausa.
- `code-smells-project/` é o projeto onde a skill é criada originalmente; nos outros
  dois ela é apenas **copiada** (`.claude/skills/refactor-arch/`), não recriada do zero.
