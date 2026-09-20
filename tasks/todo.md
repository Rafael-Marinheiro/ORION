# Tarefas — prontidão para teste do ORION

## Tarefa 1: validar dados regionais

**Descrição:** Conferir população no IBGE e distância rodoviária das 12 praças
partindo de Currais Novos.

**Critérios de aceite:**
- [x] Cada valor tem fonte e data. Ver `docs/BASE_REGIONAL.md` (20/09/2026).
- [x] Divergências do seed são listadas na base regional.

**Verificação:** pesquisa de fontes e revisão do seed.
**Dependências:** nenhuma.
**Escopo estimado:** médio.

## Tarefa 2: aplicar a base regional validada

**Descrição:** Atualizar o seed, a demanda derivada e os testes com os dados
validados.

**Critérios de aceite:**
- [x] Seed é idempotente e cria as 12 praças esperadas em base limpa.
- [x] Demanda deriva da população pela fórmula registrada. Dois testes focados passaram no Docker; suíte completa será repetida ao concluir as correções.

**Verificação:** testes focados e suíte completa em Docker.
**Dependências:** Tarefa 1.
**Escopo estimado:** médio.

## Tarefa 3: auditar RN-01 e RN-02

**Descrição:** Confrontar os requisitos de acesso e configuração com `.docx`
e com o código atual.

**Critérios de aceite:**
- [ ] Cada requisito possui evidência de código e teste, ou diagnóstico.

**Verificação:** testes focados.
**Dependências:** nenhuma.
**Escopo estimado:** pequeno.

## Tarefa 4: corrigir regras iniciais pendentes

**Descrição:** Implementar apenas os desvios confirmados na auditoria.

**Critérios de aceite:**
- [ ] Regra corrigida e protegida por teste.

**Verificação:** suíte completa em Docker.
**Dependências:** Tarefa 3.
**Escopo estimado:** médio.

## Tarefa 5: cenário ponta a ponta

**Descrição:** Cobrir o fluxo de professor, CEO e membro até o fechamento.

**Critérios de aceite:**
- [ ] Permissões e resultados pós-fechamento são verificados.

**Verificação:** teste de integração em Docker.
**Dependências:** Tarefas 2 e 4.
**Escopo estimado:** médio.

## Tarefa 6: roteiro de primeira turma

**Descrição:** Atualizar guia e checklist operacional com o fluxo validado.

**Critérios de aceite:**
- [ ] Professor consegue seguir o roteiro sem conhecimento do código.

**Verificação:** revisão manual do roteiro.
**Dependências:** Tarefa 5.
**Escopo estimado:** pequeno.
