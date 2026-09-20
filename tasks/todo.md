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
- [x] Demanda deriva da população pela fórmula registrada. Testes focados e suíte completa no Docker: 248 testes, todos passaram.

**Verificação:** testes focados e suíte completa em Docker.
**Dependências:** Tarefa 1.
**Escopo estimado:** médio.

## Tarefa 3: auditar RN-01 e RN-02

**Descrição:** Confrontar os requisitos de acesso e configuração com `.docx`
e com o código atual.

**Critérios de aceite:**
- [x] Cada requisito possui evidência de código e teste, ou diagnóstico em `docs/AUDITORIA_REGRAS_INICIAIS.md`.

**Verificação:** testes focados.
**Dependências:** nenhuma.
**Escopo estimado:** pequeno.

## Tarefa 4: corrigir regras iniciais pendentes

**Descrição:** Implementar apenas os desvios confirmados na auditoria.

**Critérios de aceite:**
- [x] Desvios de cadastro, acesso administrativo, configuração e pesos corrigidos e protegidos por testes. Migração sem senha fixa verificada em banco temporário.

**Verificação:** suíte completa em Docker.
**Dependências:** Tarefa 3.
**Escopo estimado:** médio.

## Tarefa 5: cenário ponta a ponta

**Descrição:** Cobrir o fluxo de professor, CEO e membro até o fechamento.

**Critérios de aceite:**
- [x] `test_primeira_turma`: duas equipes, três rodadas, permissões, auditoria, D+1, produção, venda, sigilo nas telas, fechamento idempotente, classificação e exportações.

**Verificação:** teste de integração em Docker.
**Dependências:** Tarefas 2 e 4.
**Escopo estimado:** médio.

## Tarefa 6: roteiro de primeira turma

**Descrição:** Atualizar guia e checklist operacional com o fluxo validado.

**Critérios de aceite:**
- [x] Roteiro do professor/aluno separado da preparação técnica em `docs/RUNBOOK_OPERACAO.md`. Revisão manual do texto concluída; execução humana ainda necessária.

**Verificação:** revisão manual do roteiro.
**Dependências:** Tarefa 5.
**Escopo estimado:** pequeno.

## Resultado da execução — 20/09/2026

- 248 testes Django no Docker, todos passaram. Cobertura: núcleo 93%
  (gate 90%), periférico 85% (gate 70%).
- Migrações sem mudanças pendentes, `check` sem problemas, seed aplicado
  duas vezes no banco local antes vazio: 12 praças e 36 demandas.
- `tools/verificar_base_limpa.py`: migrações reais em banco temporário,
  seed idempotente e nenhuma conta criada automaticamente.
- `docker-compose.turma.yml`: configuração validada, volume persistente
  para o banco local e serviço de fechamento a cada cinco segundos.
- Não foi iniciada partida real nem cadastrada turma. A senha da conta
  administrativa criada pela migração antiga foi invalidada; o responsável
  precisa redefini-la interativamente, conforme o roteiro.

## Complemento operacional — execução seguinte de 20/09/2026

Fontes relidas: DOCX 3 (RF.05/RNF.05), 8 (§8.2/§8.5), 11 (§11.1/§11.3)
e guia de implementação. Não altera fórmulas nem decisões pedagógicas.

- [x] Corrigir sorteio agendado que ignorava o jogo e pulava turmas com o
  mesmo número de rodada. Regressão reproduzida antes da correção; oito
  testes de comandos e primeira turma passaram depois.
- [ ] Verificar recuperação do fechamento após falha e corrigir gravações
  parciais, se confirmadas, antes do ensaio do processador automático.
- [ ] Ensaiar inicialização HTTP e ciclo de rodadas em base descartável.

## Pendências registradas (prosseguir sem inventar decisões)

1. **Dr. Pio — B8/B10/B9/D11:** ratificar SD 60/40, limiar regional de 200 km,
   giro contado em dois eixos e variedade de eventos. Há discrepância entre
   o guia (pendente) e o código já existente (implementado). Preservado o
   comportamento encontrado. Não certificar ranking como nota oficial.
2. **Instituição:** conferir e-mails no cadastro. Domínios permitidos não
   constam nos documentos; bloqueio automático aguarda lista caso necessário.
3. **Responsável técnico:** definir senha do professor e executar o ensaio
   de navegador/rede/rodada curta do runbook antes da presença dos alunos.
   Testes automatizados não substituem essa verificação ambiental.
4. **Escopo posterior:** certificar personalização de máquinas/estoques,
   API administrativa como alternativa às telas e teste de carga da turma.
   O cenário aprovado usa padrões RN-02 e telas web.
