# Template do Relatório de Auditoria

Formato fixo da **Fase 2**. Dois destinos, mesmo conteúdo: imprimir no console e salvar
em `reports/audit-project-N.md`. O que muda de projeto para projeto são o nome e os
findings — a estrutura abaixo é sempre a mesma.

## Formato

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-projeto>
Stack:   <Linguagem> + <Framework>
Files:   <N> analyzed | ~<L> lines of code

## Summary
CRITICAL: <N> | HIGH: <N> | MEDIUM: <N> | LOW: <N>

## Findings

### [CRITICAL] <Título curto do anti-pattern (nome do catálogo)>
**File:** `<caminho/arquivo.ext>:<linha-início>[-<linha-fim>]`
**Description:** <1–2 frases, citando o trecho problemático ou o comportamento.>
**Impact:** <consequência concreta: segurança, manutenção, performance.>
**Recommendation:** <ação específica — ex: "substituir por prepared statement".>

### [CRITICAL] <Título>
...

### [HIGH] <Título>
...

### [MEDIUM] <Título>
...

### [LOW] <Título>
...

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Regras de preenchimento, campo a campo

| Campo | Regra |
|---|---|
| Ordem dos findings | CRITICAL → HIGH → MEDIUM → LOW; dentro da mesma severidade, por arquivo e depois por linha. |
| **File** | Caminho relativo ao projeto + linha. Bloco inteiro? Use `arquivo.py:10-45`. Nunca "arquivo inteiro" sem número de linha. |
| **Description** | Descreve o código/comportamento, não a severidade — não escreva "isso é crítico porque..." (a tag já diz isso). |
| **Impact** | Consequência real e específica — "SQL injection → acesso não autorizado a todos os dados"; "N+1 → latência cresce linearmente com usuários". Nunca genérico. |
| **Recommendation** | Ação concreta, não princípio. "Usar boas práticas de segurança" é inválido; "mover `SECRET_KEY` para variável de ambiente lida em `config.py`" é válido. |
| **Título** | Usa a taxonomia do catálogo (`SQL Injection`, `God Class`, `N+1 Query`, `Hardcoded Credentials`...) — não invente nome novo para um anti-pattern já catalogado. |

## Exemplo preenchido

```markdown
### [CRITICAL] Hardcoded Credentials
**File:** `app.py:7`
**Description:** `SECRET_KEY = "minha-chave-super-secreta-123"` hardcoded no bootstrapping da aplicação. A mesma chave aparece também como campo `secret_key` na resposta de `/health` (controllers.py:289), sendo retornada ao cliente.
**Impact:** Qualquer pessoa com acesso ao repositório (ou ao endpoint `/health`) pode forjar sessões/tokens assinados com essa chave.
**Recommendation:** mover para variável de ambiente `FLASK_SECRET_KEY` carregada em `src/config/settings.py`. Remover do output de `/health`.
```

## Fechamento e persistência

- Depois de `## Findings`, sempre feche com `Total: N findings` entre separadores, e a
  linha literal `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` — é essa
  linha que dispara a pausa obrigatória da Fase 2.
- Grave o mesmo relatório em `reports/audit-project-<N>.md`, criando `reports/` no
  diretório pai do projeto se ainda não existir (se a skill roda de dentro do projeto,
  o caminho é `../reports/`). A cópia em disco pode terminar em `Total: N findings` —
  não precisa repetir a pergunta `[y/n]` no arquivo.
