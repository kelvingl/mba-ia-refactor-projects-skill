# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.


# Resolução do desafio

Abaixo a documentação da resolução. A parte acimna faz parte do README original

## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente

## 1. Análise manual

Detecções feitas manualmente, com base na leitura do código. 

### Projeto `code-smells-project`
| # | Problema                                                 | Severidade | Linha                                        | Justificativa |
| - | -------------------------------------------------------- | ---------- | -------------------------------------------- | -------------- |
| 1 | Secret hardcoded                                         | CRITICAL   | `app.py:7`                                   | Permite forjar sessões se o repositório for exposto. |
| 2 | Retorno de dados sensíveis ao cliente                    | CRITICAL   | `controllers.py:289`; `models.py:83, 99`     | Senha e configs internas vazam em respostas JSON. |
| 3 | SQLInjection possível em quase todos os metodos da model | CRITICAL   | `models.py:28,47-50,57-61,68,92,109-111,...` | Input concatenado em SQL permite manipular/destruir o banco. |
| 4 | Sem tratamento de erro centralizado, falta padronização  | HIGH       | `controllers.py` (várias funções)            | Dificulta debugging e gera respostas inconsistentes ao cliente. |
| 5 | Validação duplicada de produtos                          | MEDIUM     | `controllers.py:24-96`                       | Regra repetida em 2 lugares gera risco de divergência ao alterar. |
| 6 | Query N+1 (em for)                                       | MEDIUM     | `models.py:171-201,203-233`                  | Uma query por item em loop degrada performance em produção. |
| 7 | Magic numbers                                            | LOW        | `models.py:256-262`                          | Números sem nome dificultam entendimento e ajustes seguros. |
| 8 | Concatenação manual de string para mensagem              | LOW        | `controllers.py:8,11,57,106,161,179,208-210` | Dificulta padronização e busca em logs. |

### Projeto `ecommerce-api-legacy`
| # | Problema                                                   | Severidade | Linha                                  | Justificativa |
| - | ---------------------------------------------------------- | ---------- | -------------------------------------- | -------------- |
| 1 | Segredos hardcoded                                         | CRITICAL   | `utils.js:1-7`                         | Expõe senha do banco e chave de pagamento a qualquer leitor do código. |
| 2 | God Class concentrando regra de negócio, db e rotas        | CRITICAL   | `AppManager.js:4-141`                  | Acopla tudo em uma classe; qualquer mudança arrisca quebrar o resto. |
| 3 | Sem error handler; falta padronização de respostas de erro | HIGH       | `app.js`; `AppManager.js`              | Dificulta diagnóstico de falhas e gera respostas inconsistentes. |
| 4 | Query N+1 (em for)                                         | MEDIUM     | `AppManager.js:83-126`                 | Callbacks aninhados disparam N queries por curso/matrícula. |
| 5 | Estado global mutável sem sincronização                    | MEDIUM     | `utils.js:9-10,`; `AppManager.js:2,59` | Cache/contadores compartilhados podem corromper dados em concorrência. |
| 6 | Banco de dados em memória                                  | LOW        | `AppManager.js:7`                      | Dados são perdidos a cada reinício do servidor. |
| 7 | Log do número do cartão                                    | LOW        | `AppManager.js:45`                     | Expor dado de cartão em log viola práticas básicas de PCI-DSS. |

### Projeto `task-manager-api`
| # | Problema                                                     | Severidade | Linha                                                  | Justificativa |
| - | ------------------------------------------------------------ | ---------- | ------------------------------------------------------ | -------------- |
| 1 | Segredos hardcoded                                           | CRITICAL   | `app.py:13`; `notification_service.py:9-10`            | Permite que qualquer um com acesso ao código assuma sessões ou envie notificações falsas. |
| 2 | Retorno de dados sensíveis ao cliente                        | CRITICAL   | `user.py:17-25` + várias rotas                         | Senha/hash do usuário vaza em respostas que nunca deveriam expô-la. |
| 3 | Sem error handler centralizado, falta padronização           | HIGH       | `task_routes.py` (várias funções)                      | `except:` genérico misturado com específico dificulta rastrear falhas. |
| 4 | Regra  de validação "overdue" duplicada                      | MEDIUM     | `report_routes.py`; `task_routes.py`; `user_routes.py` | Copiada em 3 arquivos; corrigir em um não corrige nos outros. |
| 5 | Query N+1 (em for)                                           | MEDIUM     | `task_routes.py:41-57`; `report_routes.py:53-68`       | Uma query por task em loop degrada performance com a base de dados. |
| 6 | Código não usado `generate_id`, `process_task_data`          | LOW        | `helpers.py`                                           | Funções mortas aumentam manutenção e confundem novos devs. |
| 7 | Comparação de tipo com type(x) == 'str' em vez de isinstance | LOW        | `task_routes.py:141,210`; `helpers.py:103`             | Falha silenciosamente com subclasses; anti-idiomático em Python. |

## 2. Desenvolvimento da skill

### Princípios arquiteturais aplicados

**Validação pós-transformação no pipeline.** A Fase 3 conclui-se com steps de verificação: boot da aplicação, curl em 2-3 endpoints originais, encerramento do servidor. Isso evita o cenário em que refatoração parece completa mas deixa a aplicação quebrada.

**Playbook com exemplos bilíngues.** O arquivo de estratégias de refatoração inclui transformações lado-a-lado em Python e Node.js para cada anti-pattern crítico, garantindo que a skill saiba como agir independentemente da linguagem-alvo.

**Detecção orientada por sinais precisos.** Ao invés de usar heurísticas vagas como "procure por código ruim", o catálogo lista exatamente o que buscar: patterns de regex, chamadas de função específicas, estruturas de diretório. Isso reduz o espaço de interpretação do modelo.

**Pausa explícita e confirmação obrigatória.** Entre a Fase 2 (auditoria) e a Fase 3 (refatoração), o SKILL.md emite uma string literal de pausa — `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` — e aguarda resposta. Nenhuma modificação de código ocorre sem consentimento do usuário.

**Separação entre orquestração e conhecimento.** O SKILL.md mantém-se enxuto, focando em decisões procedurais: quais fases executar, quando pausar, qual referência consultar em cada momento. Os arquivos em `references/` concentram conteúdo factual — catálogo de problemas, templates, exemplos código — evitando inflação do contexto inicial.

### Agnóstica de tecnologia — mecanismo de execução

A skill consegue funcionar em 3 stacks diferentes através de 4 camadas de adaptação:

1. **Diretrizes MVC descritivas, não prescritivas.** O arquivo `mvc-guidelines.md` foca em responsabilidades (Models: abstraem dados; Controllers: orquestram fluxo; Routes: mapeiam HTTP), não em nomes de arquivo rígidos. Permite que projeto Python use `models/produto.py` e Node use `models/Product.js` — os princípios valem para os dois.

2. **Exemplos de código em ambos idiomas.** O playbook apresenta transformação idêntica em sintaxe Python e Node lado-a-lado, evitando ambiguidades.

3. **Detecção de linguagem em layers.** O arquivo `project-analysis.md` implementa uma cascata: manifesto (requirements.txt → Python, package.json → Node, pom.xml → Java), depois framework (imports/requires), depois banco (drivers), fallback para extensão de arquivo.

4. **Sinais grep-ables multilíngues.** O catálogo lista padrões de busca em múltiplas sintaxes. Ex.: SQL Injection mapeia `cursor.execute("..." + var)` (Python) e template literals `SELECT ... ${id}` (Node).

### Arquitetura e composição da skill

A skill `refactor-arch` foi organizada em uma estrutura modular, com o arquivo principal `SKILL.md` e um conjunto de referências que fornecem conhecimento de domínio profundo:

```
.claude/skills/refactor-arch/
├── SKILL.md                              # Orquestração das 3 fases (análise → auditoria → refatoração)
└── references/
    ├── project-analysis.md               # Heurísticas para identificar linguagem, framework e banco
    ├── anti-patterns-catalog.md          # 23 anti-patterns distribuídos em severidades + 8 APIs deprecated
    ├── report-template.md                # Estrutura padronizada para saída da Fase 2
    ├── mvc-guidelines.md                 # Padrão MVC alvo e responsabilidades por camada
    └── refactoring-playbook.md           # 14 estratégias de transformação com exemplos antes/depois
```

A skill é criada originalmente em `code-smells-project/.claude/skills/refactor-arch/` e distribuída para os demais projetos através de **links simbólicos**. Isso garante uma única fonte de verdade: qualquer atualização no arquivo original é automaticamente refletida em `ecommerce-api-legacy/.claude/skills/refactor-arch/` e `task-manager-api/.claude/skills/refactor-arch/`, evitando duplicação de código e inconsistências entre as três execuções.

### Desafios encontrados e soluções

**Porta 5000 ocupada em macOS.** Durante validação, `localhost:5000` já estava em uso (AirPlay Receiver). Solução: documentar fallback `PORT=5055` e sugerir verificação com `lsof -i :5000`.

**Detecção falha no Projeto 3.** Por já ter `models/` e `routes/`, poderia ser classificado como "já MVC, pule refatoração". Solução: adicionar categoria intermediária ("Parcialmente organizada, com violações") e regra: ter pastas não basta; precisa haver separação real de responsabilidades.

**Pausa fraca entre fases.** O primeiro rascunho do SKILL.md era ambíguo sobre a obrigatoriedade de parar antes da refatoração. Solução: emitir uma string exata e formatada, com instruções em negrito para o agente parar e não continuar.

**Over-engineering em Fase 3.** Primeira tentativa incluía Repository Pattern + Unit of Work + DI container — muito para projetos de 4 endpoints. Solução: documentar explicitamente no `mvc-guidelines.md`: "não criar `services/` sem necessidade; não inventar camadas que não rodam lógica."

### Catálogo de anti-patterns — cobertura e severidades

O catálogo contém **23 anti-patterns** distribuídos em 4 níveis de severidade, além de **8 APIs deprecated** que merecem flagging especial:

**CRITICAL (6 itens):**
- Debug mode ativado em produção
- Endpoint de SQL arbitrária (sem validação)
- God Class (arquivo único com DB, lógica, e rotas)
- Passwords em plaintext ou hash fraco (MD5, SHA1)
- Credenciais hardcoded ("SECRET_KEY =", chaves em variáveis)
- SQL Injection (SQL direto concatenado)

**HIGH (6 itens):**
- Autenticação fraca ou ausente
- Integridade referencial quebrada (foreign keys sem constraint)
- Ausência de centralização de tratamento de erros
- Callback Hell (promises aninhadas, chained callbacks)
- Estado global mutável sem encapsulamento
- Lógica de negócio prisioneira em rotas/controllers

**MEDIUM (6 itens):**
- Validação de input ausente nas rotas
- Serialização inconsistente (alguns objetos retornam IDs, outros nomes)
- `except:` nú (capturando Exception genérica)
- Falta de paginação em endpoints que retornam listas
- Validação duplicada entre camadas
- Queries N+1 (sem JOIN, loop de selects)

**LOW (5 itens):**
- Comparação de tipo usando `type(x) == list`
- Concatenação manual de strings em mensagens de erro
- Print statements para logging
- Nomes de variáveis confusos ou genéricos
- Magic numbers soltos no código

**APIs Deprecated (8):**
- Versões antigas de Flask-SQLAlchemy
- `utcnow()` como default em coluna de timestamp
- `SQLALCHEMY_TRACK_MODIFICATIONS` não configurado
- `body-parser` legacy em Express
- `datetime.strptime()` nú sem tz awareness
- `request.get_json()` sem `silent=True`
- SQLite3 com callbacks (padrão antigo)
- `datetime.utcnow()` (usar `now(timezone.utc)`)

**Motivo dessa seleção:** foram os anti-patterns reais encontrados durante análise manual dos 3 projetos. Juntos, cobrem as 4 severidades com margem, e os deprecated APIs ajudam a surfar dívidas técnicas silenciosas (ex.: `datetime.utcnow()` aparecia 13 vezes no Projeto 3 sem aviso óbvio).

### Playbook de refatoração — padrões de transformação

O arquivo `refactoring-playbook.md` contém **14 padrões** (PB-1 a PB-14) que cobrem as transformações mais críticas:

- Substituição de print por logger estruturado
- Movimentação de validação para schemas/constantes
- Atualização de `datetime.utcnow()` para timezone-aware
- Enforcement de integridade referencial com cascata/serviço
- Estado global → Factory pattern
- Centralização de try/except em error handler global
- Conversão de N+1 queries em JOINs
- Transformação de callback hell em async/await
- Elevação de lógica de rota para controller
- Decomposição de God Class em camadas (models, controllers, services)
- Hash forte + omissão de senhas em responses
- Substituição de SQL direto por prepared statements
- Remoção de endpoints de admin arbitrários
- Extração de config para módulo + variáveis de ambiente

Cada padrão inclui exemplo Python e Node.js (quando aplicável), mostrando estrutura antes/depois.

Agora, com a skill construída e testada, os 3 projetos podem ser refatorados de forma reproduzível e confiável.

## 3. Resultados

### 3.1 Resumo dos relatórios de auditoria (Fase 2)

Números extraídos diretamente da seção `## Summary` de cada relatório em `reports/`:

| Projeto | Stack detectada | Arquivos analisados | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|---|
| 1 — `code-smells-project` | Python + Flask 3.1.1 | 4 | 6 | 3 | 2 | 1 | 10 |
| 2 — `ecommerce-api-legacy` | Node.js + Express ^4.18.2 | 3 | 3 | 6 | 3 | 3 | 15 |
| 3 — `task-manager-api` | Python + Flask 3.0.0 + SQLAlchemy | 13 | 5 | 4 | 7 | 4 | 20 |

Os 3 projetos superam com folga o mínimo de 5 findings e todos incluem pelo menos 1 CRITICAL/HIGH — os critérios de aceite obrigatórios da Fase 2 são atingidos nos 3.

Observações sobre a distribuição:

- **Projeto 1** concentra a maior densidade de CRITICAL (6 de 10 findings) porque o código original tinha falhas de segurança propositalmente graves e concentradas (endpoint de SQL arbitrário, SQL Injection generalizado, senha em texto plano, debug mode, secret hardcoded) além de um único arquivo (`models.py`) acumulando toda a lógica.
- **Projeto 2** é o único com mais HIGH que CRITICAL — reflexo do callback hell e da lógica de negócio presa nas rotas do `AppManager.js`, mais do que falhas isoladas de segurança pontual.
- **Projeto 3** tem o maior total (20) mesmo já tendo `models/`, `routes/`, `services/`, `utils/` — prova de que separação de pastas não é sinônimo de arquitetura correta. A skill identificou 2 APIs deprecated (`datetime.utcnow()` usado direto e como `default=`/`onupdate=` de coluna) que só aparecem porque o catálogo cobre detecção de deprecated APIs explicitamente.

### 3.2 Comparação antes/depois da estrutura

**Projeto 1 — `code-smells-project`**

```
Antes                          Depois
------------------------       ------------------------------------
app.py                         app.py                (composition root, delega a src/app.py)
controllers.py                 src/
database.py                    ├── app.py            (application factory)
models.py                      ├── config/settings.py         (SECRET_KEY/DEBUG via env)
requirements.txt                ├── models/           (database.py, produto_model.py, usuario_model.py, pedido_model.py)
                                ├── controllers/       (produto_, usuario_, pedido_, relatorio_controller.py)
                                ├── views/routes.py    (blueprints)
                                ├── middlewares/error_handler.py
                                └── utils/security.py  (hash de senha, prepared statements)
```

`app.py`, `controllers.py`, `models.py` e `database.py` na raiz foram mantidos como referência histórica de "antes", mas não são mais importados por nenhum módulo da aplicação — o entry point real (`app.py` → `create_app()`) delega inteiramente para `src/`.

**Projeto 2 — `ecommerce-api-legacy`**

```
Antes                          Depois
------------------------       ------------------------------------
src/app.js                     src/
src/AppManager.js               ├── app.js            (entry point)
src/utils.js                    ├── config/index.js   (PAYMENT_GATEWAY_KEY/ADMIN_TOKEN via env)
                                ├── models/            (db.js, user.model.js, course.model.js, enrollment.model.js)
                                ├── controllers/        (checkout.controller.js, report.controller.js, user.controller.js)
                                ├── routes/             (checkout.routes.js, report.routes.js, user.routes.js, index.js)
                                ├── middlewares/         (errorHandler.js, asyncHandler.js, requireAdmin.js)
                                └── utils/               (crypto.js — bcrypt, logger.js)
```

O God Class `AppManager.js` (141 linhas, 8+ responsabilidades) foi decomposto nas 4 camadas acima; `badCrypto` (base64 em loop) virou `bcryptjs`; rotas administrativas ganharam middleware `requireAdmin`.

**Projeto 3 — `task-manager-api`**

```
Antes                           Depois
------------------------        ------------------------------------
app.py, database.py, seed.py    app.py, seed.py                (entry points mantidos)
models/ (task, user, category)  config/settings.py              (novo — SECRET_KEY/SMTP via env)
routes/ (task_, user_,          models/ (+ database.py)
         report_routes)         controllers/ (task_, user_, report_controller.py)   ← novo
services/notification_service   views/ (task_, user_, report_routes.py)            ← routes/ renomeado
utils/helpers.py                schemas/ (task_schema.py, user_schema.py)          ← novo
                                 middlewares/error_handler.py                       ← novo
                                 services/notification_service.py                   (mantido)
                                 utils/helpers.py                                   (mantido)
```

Este foi o caso de "MVC parcial → MVC completo": a skill reconheceu que `models/`/`routes/` já existiam, então a Fase 3 não recriou tudo do zero — extraiu a lógica de negócio das rotas gordas para `controllers/`, moveu validação para `schemas/`, centralizou erro em `middlewares/` e corrigiu as falhas de segurança (MD5 → hash forte, senha removida do `to_dict()`, `SECRET_KEY`/SMTP para env).

### 3.3 Checklist de validação preenchido

O mesmo checklist do enunciado foi aplicado aos 3 projetos após a Fase 3. Todos os itens foram verificados manualmente (boot real da aplicação + chamadas `curl` nos endpoints originais):

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| **Fase 1** | | | |
| Linguagem detectada corretamente | ✅ | ✅ | ✅ |
| Framework detectado corretamente | ✅ | ✅ | ✅ |
| Domínio da aplicação descrito corretamente | ✅ | ✅ | ✅ |
| Número de arquivos analisados condiz com a realidade | ✅ (4) | ✅ (3) | ✅ (13) |
| **Fase 2** | | | |
| Relatório segue o template definido nas referências | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Findings ordenados por severidade (CRITICAL → LOW) | ✅ | ✅ | ✅ |
| Mínimo de 5 findings identificados | ✅ (10) | ✅ (15) | ✅ (20) |
| Detecção de APIs deprecated incluída (se aplicável) | ➖ n/a | ✅ (sqlite3 callback API) | ✅ (2x `datetime.utcnow()`) |
| Skill pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3** | | | |
| Estrutura de diretórios segue padrão MVC | ✅ | ✅ | ✅ |
| Configuração extraída para módulo de config (sem hardcoded) | ✅ | ✅ | ✅ |
| Models criados para abstrair dados | ✅ | ✅ | ✅ |
| Views/Routes separadas para roteamento | ✅ | ✅ | ✅ |
| Controllers concentram o fluxo da aplicação | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ (`app.py`) | ✅ (`src/app.js`) | ✅ (`app.py`) |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem corretamente | ✅ | ✅ | ✅ |

### 3.4 Logs das aplicações rodando após a refatoração

**Projeto 1 — `code-smells-project`** (`python app.py`, porta 5000):

```
==================================================
SERVIDOR INICIADO
Rodando em http://localhost:5000
==================================================
 * Serving Flask app 'src.app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000

GET /                → {"mensagem": "Bem-vindo à API da Loja", "versao": "1.0.0", "endpoints": {...}}
GET /produtos         → {"sucesso": true, "dados": [ {...10 produtos...} ]}
GET /health           → {"status": "ok", "database": "connected", "ambiente": "producao",
                          "counts": {"produtos": 10, "usuarios": 4, "pedidos": 1}}
```

`Debug mode: off` e a ausência dos campos `secret_key`/`debug` no `/health` confirmam a correção dos 2 findings CRITICAL relacionados (antes, `/health` vazava a `SECRET_KEY` e a flag de debug).

**Projeto 2 — `ecommerce-api-legacy`** (`npm start`, porta 3000):

```
> desafio-arquitetura-ia-boilerplate@1.0.0 start
> node src/app.js

Frankenstein LMS rodando na porta 3000...
[INFO] 2026-09-27T15:35:52.775Z Payment processed for course 1

POST /api/checkout            → {"msg": "Sucesso", "enrollment_id": 2}
GET  /api/admin/financial-report → [{"course": "Clean Architecture", "revenue": 1994, "students": [...]}]
DELETE /api/users/2            → {"success": true, "message": "Usuário removido com sucesso."}
```

O log `[INFO] Payment processed for course 1` substitui o antigo `console.log` que expunha o número do cartão e a chave do gateway de pagamento juntos no stdout — finding LOW corrigido.

**Projeto 3 — `task-manager-api`** (`python seed.py && python app.py`, porta 5000):

```
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000

GET /tasks  → 200, lista de 10 tasks com "overdue", "user_name" e "category_name" calculados
GET /users  → 200, lista de 3 usuários — SEM o campo "password" (antes vazava o hash MD5)
GET /       → {"message": "Task Manager API", "version": "1.0"}
```

A ausência do campo `password`/`hash` na resposta de `/users` confirma a correção do finding CRITICAL "Weak Password Hash + Password Exposed in Response".

### 3.5 Observações sobre o comportamento da skill em stacks diferentes

- **Mesmo `SKILL.md`, zero edição entre projetos.** A skill foi copiada via `.claude/skills/refactor-arch/` para `ecommerce-api-legacy/` e `task-manager-api/` sem nenhuma alteração de conteúdo, e as 3 fases executaram de ponta a ponta nos 3 — confirmando o requisito de agnosticismo de tecnologia.
- **Heurística de detecção em cascata funcionou nos 2 idiomas.** `requirements.txt` → Python/Flask (projetos 1 e 3) e `package.json` → Node/Express (projeto 2) foram suficientes para a Fase 1 identificar corretamente stack, versão de framework e domínio sem ambiguidade.
- **O catálogo de anti-patterns generalizou bem entre paradigmas distintos.** O mesmo "God Class/God Module" foi detectado tanto num arquivo Python sem classes (`models.py`, funções soltas) quanto numa classe Node.js de fato (`AppManager`) — o sinal de detecção é responsabilidade misturada, não sintaxe de classe.
- **APIs deprecated são o ponto mais sensível à stack.** No projeto 2, o deprecated é `sqlite3` com API de callback (idiomático de Node antigo); nos projetos 1 e 3 (mesma linguagem), o mesmo padrão de detecção (`datetime.utcnow()`) se repete, mas só o projeto 3 teve ocorrências suficientes para virar finding — o projeto 1 não usa `datetime` na modelagem original.
- **Profundidade da Fase 3 se adaptou ao ponto de partida.** Nos projetos 1 e 2 (monólitos de 3-4 arquivos), a Fase 3 criou a árvore MVC inteira do zero. No projeto 3, que já tinha `models/`/`routes/`/`services/`/`utils/`, a skill evitou recriar o que já existia — reorganizou apenas o que violava responsabilidades (rotas gordas → controllers, validação solta → schemas) e não caiu na armadilha de classificar "já tem pastas" como "já é MVC" (risco identificado durante o desenvolvimento, ver "Desafios encontrados").
- **Pausa de confirmação se comportou de forma idêntica nos 3.** A string literal de pausa entre Fase 2 e Fase 3 apareceu sem variação de fraseado nos 3 logs de execução, confirmando que o comportamento não é afetado pela stack-alvo.