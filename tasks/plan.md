# Plano de implementação: prontidão para teste do ORION

## Visão geral

Concluir os pontos que impedem uma sessão de teste com turma: dados regionais
auditáveis, regras iniciais verificadas contra a especificação, fluxo completo
de professor e grupo validado e documentação de operação atualizada.

## Decisões de arquitetura

- A especificação em `.docx` é a fonte normativa; o guia registra a evidência
  e o resultado de cada verificação.
- Dados municipais usam a estimativa mais recente do IBGE disponível na data
  da atualização. Distâncias usam uma única fonte de rota rodoviária, anotada
  no seed para permitir repetição.
- Cada correção permanece em uma fatia vertical: regra, teste e documentação
  no mesmo incremento.

## Lista de tarefas

### Fase 1 — Base verificável

- [ ] Tarefa 1: validar populações e distâncias das praças regionais.
- [ ] Tarefa 2: atualizar o seed e testar demanda derivada e distâncias.

### Checkpoint: dados regionais

- [ ] As 12 cidades possuem fonte e data registradas.
- [ ] A suíte completa passa.

### Fase 2 — Regras iniciais e auditoria

- [ ] Tarefa 3: conferir os requisitos RN-01 e RN-02 nos `.docx` e no código.
- [ ] Tarefa 4: corrigir ou registrar como conforme senha, limites de rodadas,
  força de trabalho inicial, custo de máquina e expansão do parque.

### Checkpoint: regras iniciais

- [ ] Cada linha auditada aponta código e teste.
- [ ] A suíte completa passa.

### Fase 3 — Aceitação de uso

- [ ] Tarefa 5: automatizar um cenário ponta a ponta de professor e grupo.
- [ ] Tarefa 6: atualizar o guia e o roteiro de teste manual da primeira turma.

### Checkpoint: pronto para teste com turma

- [ ] Professor configura jogo, cria grupos e abre rodada.
- [ ] CEO compra, produz, distribui e submete; a rodada fecha e exibe relatórios.
- [ ] Membro não autorizado não consegue submeter.
- [ ] Suíte completa e checagem de migrações passam.

## Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| População e distância mudam a demanda e o frete | Alto | Registrar fonte, data e testes de valores derivados |
| Auditoria antiga diverge do código já entregue | Médio | Revalidar por evidência, sem assumir que o rótulo antigo é atual |
| Fluxos isolados passam, mas falham em sequência | Alto | Criar cenário ponta a ponta com papéis reais |

## Questão para aprovação

Este plano trata a revisão de dados regionais como calibração de teste antes
do uso em sala e mantém uma única fonte de rota rodoviária registrada no seed.
