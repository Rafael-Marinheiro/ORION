# Backlog de Implementacao ORION

## Como ler
- `Prioridade P0`: critico para aderencia ao escopo base do simulador.
- `Prioridade P1`: importante para ampliar realismo e uso pedagogico.
- `Prioridade P2`: evolucao e refinamento.
- `Status`: `TODO`, `EM_ANDAMENTO`, `CONCLUIDO`.

## P0 - Nucleo de simulacao

1. `ORION-P0-01` | `CONCLUIDO`
- Tema: Capacidade produtiva dedicada por produto (A/B/C) e tempo de maquina por linha.
- Escopo: usar `tempo_producao_min` + maquinas por linha para limitar producao por produto.
- Aceite:
  - producao de A nao consome capacidade de B/C;
  - bloqueio/ajuste automatico quando extrapolar capacidade da linha;
  - testes de limite por produto.

2. `ORION-P0-02` | `CONCLUIDO`
- Tema: Fechamento de rodada consolidado com relatorio de execucao.
- Escopo: registrar resumo estruturado (receita, custos, perdas, penalidades, market share) por grupo/rodada.
- Aceite:
  - entidade de consolidacao persistida por rodada;
  - tela de consulta por rodada;
  - exportacao PDF/Excel com campos consolidados.

3. `ORION-P0-03` | `CONCLUIDO`
- Tema: Modo CEO por rodada (nao fixo apenas por tipo de usuario).
- Escopo: definir CEO oficial por grupo e rodada, com trilha de auditoria de submissao.
- Aceite:
  - apenas CEO da rodada submete;
  - auditoria com usuario/data/hora/IP;
  - troca de CEO sem quebrar historico.

4. `ORION-P0-04` | `CONCLUIDO`
- Tema: Curva de demanda por cidade/produto com teto por produto.
- Escopo: separar demanda maxima por produto em cada cidade (hoje demanda unica por cidade).
- Aceite:
  - demanda configuravel por cidade+produto;
  - alocacao nao excede teto do produto na cidade;
  - comparativos por produto no ranking.

## P1 - Realismo operacional/financeiro

5. `ORION-P1-01` | `CONCLUIDO`
- Tema: Investimento em marketing por cidade com efeito na demanda.
- Escopo: aplicar fator de marketing por grupo/cidade no fechamento da demanda.
- Aceite:
  - formula parametrizada no sistema;
  - impacto visivel no market share;
  - testes com/sem investimento.

6. `ORION-P1-02` | `CONCLUIDO`
- Tema: Investimento em maquinas e RH com ativacao na rodada seguinte.
- Escopo: compra de maquinas por linha + necessidade de operadores (2 por maquina).
- Aceite:
  - maquinas novas entram D+1;
  - maquina sem RH fica inativa;
  - custo de RH recorrente por rodada.

7. `ORION-P1-03` | `CONCLUIDO`
- Tema: Aplicacoes financeiras (1.5%/rodada).
- Escopo: aplicar/resgatar saldo investido com juros compostos.
- Aceite:
  - movimentacao registrada no financeiro;
  - rendimento automatico por rodada;
  - bloqueios de saldo insuficiente.

8. `ORION-P1-04` | `CONCLUIDO`
- Tema: Desconto logistico cruzado (compra MP x remessa para mesma cidade).
- Escopo: aplicar desconto no custo logistico de compra quando houver envio comercial relacionado.
- Aceite:
  - regra parametrizada;
  - calculo por cidade e limite por quantidade;
  - evidenciado no resumo da rodada.

9. `ORION-P1-05` | `CONCLUIDO`
- Tema: Eventos com escopo de estado (nao apenas percentual).
- Escopo: suportar eventos de atraso, retencao de entrega, bloqueio de producao e quebra de estoque.
- Aceite:
  - modelo com tipo de efeito + duracao;
  - processamento no fechamento e/ou abertura da rodada;
  - historico do impacto aplicado.

## P1 - Produto e UX

10. `ORION-P1-06` | `CONCLUIDO`
- Tema: Tela de painel com visao gerencial por modulo.
- Escopo: reorganizar painel em blocos (MP, producao, distribuicao, financeiro, indicadores).
- Aceite:
  - layout responsivo em 320/768/1200;
  - filtros por rodada;
  - mensagens de erro/sucesso padronizadas.

11. `ORION-P1-07` | `CONCLUIDO`
- Tema: Configuracao guiada do jogo.
- Escopo: assistente de setup inicial (capital, produtos ativos, cidades, eventos, pesos ranking).
- Aceite:
  - wizard com validacao por etapa;
  - resumo final antes de salvar;
  - bloqueio de inconsistencias.

## P2 - Plataforma e governanca

12. `ORION-P2-01` | `CONCLUIDO`
- Tema: Multi-jogos/turmas com isolamento completo.
- Escopo: reforcar filtros por `jogo` em todas as telas, APIs e comandos.
- Aceite:
  - nenhuma contaminacao de dados entre jogos;
  - testes automatizados de isolamento.

13. `ORION-P2-02` | `CONCLUIDO`
- Tema: Observabilidade e auditoria.
- Escopo: logs estruturados por rodada/grupo e dashboard operacional de jobs.
- Aceite:
  - logs com correlation id;
  - historico de execucao dos comandos agendados;
  - alertas de falha.

14. `ORION-P2-03` | `CONCLUIDO`
- Tema: Cobertura de testes por regras de negocio.
- Escopo: aumentar testes para cenarios limite (empate, overflow, rodada sem envios, eventos encadeados).
- Aceite:
  - cobertura de regras criticas >= 85%;
  - suite em CI com tempos previsiveis.

## Itens concluidos recentemente
- Motor de compra/estoque de materia-prima com recebimento D+1.
- Producao com consumo de materia-prima.
- Distribuicao por produto e fechamento por demanda com curva de preco.
- Perecibilidade + armazenagem no fechamento de rodada.
- Eventos com chance igual e cooldown de 2 rodadas.
- Market share por cidade/produto e ranking multicriterio por rodada.
- Capacidade produtiva dedicada por produto (A/B/C), com bloqueio por linha e testes automatizados.
- Consolidado persistido por grupo/rodada no fechamento, com consulta em tela e exportacao PDF/Excel.
- CEO oficial por grupo/rodada com auditoria de submissao (usuario, data/hora e IP).
- Demanda maxima configuravel por cidade+produto aplicada no fechamento.
- Investimentos por categoria (marketing por cidade, maquinas/RH D+1 por linha, financeiro aplicar/resgatar).
- Rendimento automatico de aplicacoes financeiras (juros compostos por rodada).
- Desconto logistico cruzado parametrizavel na compra de materia-prima.
- Eventos com escopo de estado (atraso MP, retencao de entrega, bloqueio de producao, quebra de estoque).
- Painel reorganizado em modulos com layout responsivo e filtro por rodada.
- Wizard de configuracao inicial em 3 etapas com validacao e resumo final.
- Isolamento multi-jogo reforcado em APIs e fechamento.
- Observabilidade de jobs com `correlation_id`, historico de execucao e dashboard operacional.
- Cobertura de testes ampliada para cenarios de empate/teto/rodada sem envio/eventos e regras novas.

## Plano de release executado (2026-03-09)

1. Fechamento tecnico da versao atual - `CONCLUIDO`
- hotfixes de runtime em `views.py`/`models.py`;
- trilha de migracao limpa para CI em `app/migrations_ci` com `settings_ci`;
- validacao de `migrate + seed + check` em ambiente isolado.

2. Pipeline de qualidade (CI) - `CONCLUIDO`
- workflow atualizado para:
  - `compileall`;
  - `makemigrations --check` (trilha principal e trilha CI);
  - `migrate + seed + check` em ambiente limpo;
  - testes automatizados com gate de cobertura critica `>=85%`.

3. Teste ponta a ponta dos fluxos principais - `CONCLUIDO`
- suite estabilizada para 70 testes passando;
- testes de fluxo GM/Grupo mantidos e atualizados;
- testes adicionais de servicos criticos adicionados.

4. Hardening de operacao - `CONCLUIDO`
- runbook/checklists alinhados com fluxo de operacao e recuperacao.

5. Preparacao de release - `CONCLUIDO`
- changelog/versionamento revisados;
- base pronta para congelamento de versao e tag.
