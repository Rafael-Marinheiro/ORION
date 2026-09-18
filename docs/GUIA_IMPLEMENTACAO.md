# Guia de Implementação ORION

Documento único de referência para levar o simulador à conformidade com a
especificação. Substitui `SPRINTS.md` e `docs/BACKLOG.md` como fonte de
verdade sobre o que está feito — os dois continuam no repositório como
histórico, mas não devem ser consultados para decidir o que falta.

Última auditoria: **2026-09-18**.

---

## 1. Por que este documento existe

O `docs/BACKLOG.md` declarava os 14 itens como `CONCLUIDO`. A auditoria de
2026-09-18 conferiu cada regra da especificação contra o código e encontrou
itens marcados como concluídos que estão divergentes, incompletos ou que
quebravam em execução.

A causa não é descuido: o backlog rastreava **entrega de sprint**, não
**conformidade com a especificação**, e nada checava a diferença. Um item
entrava como concluído quando a funcionalidade existia, ainda que a regra
implementada não fosse a do documento.

Este guia corrige isso com um vocabulário de status que distingue os dois
casos:

| Status | Significado |
|---|---|
| `CONFORME` | Implementado e confere com a especificação. Verificado no código. |
| `DIVERGENTE` | Implementado, mas a regra difere da especificação. |
| `AUSENTE` | A especificação exige e não existe no código. |
| `BLOQUEADO` | A especificação se contradiz. Precisa de decisão antes de codar. |
| `NAO_VERIFICADO` | Ainda não auditado. Não presuma nada. |

Regra de ouro: **nada vira `CONFORME` sem o trecho de código e o teste que
provam.** Se não dá para apontar os dois, o status é `NAO_VERIFICADO`.

---

## 2. Fonte da verdade

A especificação está em `_documentação/TXT/` (15 documentos). A versão `.docx`
em `_documentação/DOC/` tem o mesmo conteúdo.

Quando o documento e o código discordam, **o documento vence** — exceto nos
itens da seção 3, onde o próprio documento se contradiz e só o autor da
especificação (Dr. Pio Marinheiro) pode decidir.

---

## 3. Bloqueadores — a especificação se contradiz

Estes cinco pontos impedem "implementar 100% da documentação", porque há duas
versões incompatíveis escritas. Precisam de decisão registrada antes de virar
código.

| # | Tema | Versão A | Versão B | O código faz hoje | Decisão |
|---|---|---|---|---|---|
| B1 | Composição dos produtos | §6.1: A = 120 kg MP1 + 40 MP2 + 60 MP3 + 80 MP4 | §13.2: A = 2 un MP1 + 1 un MP2 | Versão A | pendente |
| B2 | Perecibilidade | §6.2: A não perece, B perece em 1 rodada, C não perece | §13.8: todos os produtos valem 2 rodadas | Versão A | pendente |
| B3 | Capacidade de máquina | §13.4: 400 min por máquina por rodada | RN-06: turno único de 87 h = 5.220 min | Versão A (400) | pendente |
| B4 | Eventos por rodada | §8.2: exatamente 1, probabilidades somam 100% | RN-10: até 2 simultâneos | Versão A (1) | pendente |
| B5 | Critério de desempate | §12.5: EO → SD → DS → Receita bruta → alfabética | RN-12: lucro acumulado → market share → caixa → penalidades → alfabética | — | pendente |

Observações que ajudam a decidir:

- **B1 e B2**: adotar a Versão B exigiria refazer o seed, as composições e o
  cálculo de custo de produção. A Versão A já está implementada e é a que os
  números de custo estimado do §6.1 sustentam.
- **B3**: existe ainda um terceiro valor solto no código — `GameConfig.capacidade_maquina`
  tem default `100`, que não corresponde a nenhuma das duas versões e parece
  não ser usado no cálculo real. Seja qual for a decisão, esse campo precisa
  ser removido ou alinhado.
- **B4**: é o Sprint 29 já conhecido. A Versão A está implementada.
- **B5**: nenhum dos dois conjuntos está implementado como descrito; ver `ORION-C-07`.

---

## 4. Matriz de conformidade

### 4.1 Cadastro, acesso e configuração

| Regra | Origem | Status | Onde |
|---|---|---|---|
| Perfis aluno / CEO / professor | RF.01 | `CONFORME` | `models.User.tipo_usuario` |
| CEO por rodada, só ele submete | RF.01, RN-03 | `CONFORME` | `models.CEOGrupoRodada`, `PainelGrupoView` |
| Auditoria de submissão (usuário, data/hora, IP) | RF.01 | `CONFORME` | `models.AuditoriaSubmissaoRodada` |
| Grupo com 3 a 6 participantes | RN-02 | `CONFORME` | `forms.MembroFormSet` (`min_num=3`, `max_num=6`) |
| Capital inicial R$ 1.000.000 | RN-02 | `CONFORME` | `GameConfig.capital_inicial` |
| 40 máquinas iniciais (15 A / 15 B / 10 C) | RN-02 | `CONFORME` | `views.CAPACIDADE_PADRAO_POR_CODIGO` |
| 80 funcionários iniciais (2 por máquina) | RN-02 | `NAO_VERIFICADO` | — |
| Senha mínima de 8 caracteres com letras e números | RN-01 | `NAO_VERIFICADO` | — |
| Número de rodadas entre 3 e 12 | RN-02 | `AUSENTE` | sem validação no formulário |

### 4.2 Produção

| Regra | Origem | Status | Onde |
|---|---|---|---|
| Máquinas dedicadas por linha, sem compartilhar | §13.4 | `CONFORME` | `CapacidadeProdutoGrupo` |
| Tempo por unidade: A 2 min, B 4 min, C 5 min | §13.3 | `CONFORME` | seed `produtos` |
| Máquina sem 2 operadores não produz | §14.3, RN-06 | `CONFORME` | `capacidade_unidades_rodada`: `min(maquinas, operadores // 2)` |
| Produção parcial quando falta MP ou tempo | §13.7 | `CONFORME` | `fechar_rodadas` |
| Só unidades inteiras | §6.3 | `CONFORME` | `int(minutos_total // tempo)` |
| Custo de produção = MP consumida | §13.9 | `CONFORME` | `services/producao.py` |
| Capacidade por máquina | §13.4 vs RN-06 | `BLOQUEADO` | ver B3 |

### 4.3 Matéria-prima e logística

| Regra | Origem | Status | Onde |
|---|---|---|---|
| 4 MPs com preços 3,00 / 5,50 / 8,00 / 15,00 | §7.1 | `CONFORME` | seed `materias_primas` |
| Recebimento na rodada seguinte (D+1) | §7.2 | `CONFORME` | `CompraMateriaPrima.rodada_pedido` |
| Frete de MP a R$ 1,50/km | §7.2 | `CONFORME` | `services/materias_primas.calcular_frete` |
| Armazenagem de MP a 2% do valor de compra | §7.4 | `CONFORME` | `fechar_rodadas` |
| Fornecedores por cidade | §7.1 | `CONFORME` | `views.MATERIA_PRIMA_FORNECEDORES` |
| Desconto logístico cruzado de R$ 0,50/km | §7.2.1 | `DIVERGENTE` | **duas implementações conflitantes**: `services/materias_primas.py` usa R$ 0,50/km (correto), `views.FATOR_DESCONTO_LOGISTICO_CRUZADO` usa 10% |
| Frete de produtos acabados | §9.2a | `DIVERGENTE` | `economia_service` usa R$ 0,10/km/unidade — taxa que não consta em nenhum documento |

### 4.4 Comercialização e demanda

| Regra | Origem | Status | Onde |
|---|---|---|---|
| 10 cidades com distância e demanda máxima | §9.1 | `CONFORME` | seed `cidades` |
| Curva de sensibilidade a preço 5x / 3x / 2x / 1x / 0,5x | §9.2c | `CONFORME` | `fechar_rodadas.calcular_peso_preco` |
| Alocação proporcional ao peso, limitada ao enviado | §9.2b, §9.2c | `CONFORME` | `fechar_rodadas` |
| Demanda máxima por cidade e produto | §9.1 | `CONFORME` | `DemandaCidadeProduto` |
| Armazenagem de produtos a 2% do custo unitário | §6.4 | `CONFORME` | `fechar_rodadas` |
| Perecibilidade do produto B (1 rodada) | §6.2 | `CONFORME` | `Produto.validade_rodadas` |

### 4.5 Investimentos

| Regra | Origem | Status | Onde |
|---|---|---|---|
| Máquinas ativam na rodada seguinte | §14.2.2 | `CONFORME` | `Investimento.rodada_ativacao` |
| Aplicação financeira a 1,5% por rodada, juros compostos | §14.4 | `CONFORME` | `TAXA_APLICACAO_FINANCEIRA_RODADA` |
| Fator de marketing logarítmico, teto +20%, satura em R$ 10.000 | §14.1.1 | `DIVERGENTE` | `views.calcular_fator_marketing` usa modelo linear por `ganho_por_base` |
| Salário do operador R$ 1.800/mês | §14.2.4, §14.3 | `DIVERGENTE` | `CUSTO_OPERADOR_POR_RODADA = 2000` |
| Custo da máquina R$ 8.000 | §14.2.4 | `NAO_VERIFICADO` | — |
| Limite de expansão de +50% sobre as máquinas iniciais | §14.2.1 | `AUSENTE` | sem validação |

### 4.6 Eventos aleatórios

| Regra | Origem | Status | Onde |
|---|---|---|---|
| Sorteio automático por rodada | §8.2 | `CONFORME` | `views.sortear_evento` + comando agendado |
| Evento aplicado igualmente a todos os grupos | §8.2 | `CONFORME` | `EventoRodada` por rodada |
| Os 6 eventos nomeados do §8.4 | §8.4 | `AUSENTE` | o seed cria outros eventos |
| Probabilidades 15 / 20 / 20 / 15 / 15 / 15 | §8.4 | `DIVERGENTE` | seed aplica **probabilidade igual** a todos |
| Impactos específicos por evento (ex.: greve retém 30% das entregas) | §8.4 | `DIVERGENTE` | impactos genéricos |
| Frase indicativa por evento | §8.5 | `AUSENTE` | campo não existe no modelo |
| Até 2 eventos simultâneos | RN-10 | `BLOQUEADO` | ver B4 |

### 4.7 Fechamento, financeiro e ranking

| Regra | Origem | Status | Onde |
|---|---|---|---|
| Fechamento automático no prazo | §11.1 | `CONFORME` | comando `fechar_rodadas` agendado |
| Bloqueio de edição após o prazo | §11.1 | `CONFORME` | `permite_edicao` |
| Penalidade de 10% por não submeter | §11.2, RN-04 | `CONFORME` | `services/fechamento.py` (aplica sobre `grupo.capital`; a spec diz "caixa ao final da rodada anterior" — diferença menor, vale ratificar) |
| Decisões omitidas repetem a rodada anterior | §11.2 | `CONFORME` | `services/fechamento.py` |
| Consolidado persistido por grupo e rodada | §11.3d | `CONFORME` | `ConsolidadoRodadaGrupo` |
| Ranking multicritério de 5 eixos (EO, DF, EE, SD, DS) | §12.2 | `DIVERGENTE` | implementa 4 eixos: lucro 0,4 · market share 0,3 · atendimento 0,2 · estoque 0,1. **Sustentabilidade não existe** |
| Pesos 0,30 / 0,25 / 0,15 / 0,20 / 0,10 | §12.4 | `DIVERGENTE` | ver acima |
| Critérios de desempate | §12.5 vs RN-12 | `BLOQUEADO` | ver B5 |
| Restrição de investimento após 2 rodadas de caixa negativo | RN-09 | `AUSENTE` | — |

### 4.8 Telas (§10)

| Tela | Perfil | Status | Rota |
|---|---|---|---|
| Inicial | todos | `CONFORME` | `/` |
| Login | todos | `CONFORME` | `/login/` |
| Painel do grupo | CEO, membro | `CONFORME` | `/painel/` |
| Decisões por rodada | CEO | `CONFORME` | integrado ao painel |
| Relatórios financeiros | todos | `DIVERGENTE` | `/relatorios/` — falta DRE e Fluxo de Caixa |
| Configuração do jogo | professor | `CONFORME` | `/config/`, `/config/wizard/` |
| Abrir rodada | professor | `CONFORME` | `/abrir_rodada/` |
| Grupos | professor | `CONFORME` | `/grupos/` |
| Ranking | todos | `DIVERGENTE` | `/ranking/` — falta destaques da rodada e evolução do grupo |
| Ajuda | todos | `CONFORME` | `/ajuda/` |
| **Encerramento da rodada** | CEO | `AUSENTE` | template existe (`financeiro/encerramento.html`), sem view nem rota |
| **Relatórios comparativos** | todos | `AUSENTE` | templates existem (`dashboard/*.html`), sem view nem rota |
| **Classificação final** | todos | `AUSENTE` | template existe (`classificacao.html`), sem view nem rota |
| **Gerenciamento do jogo** (monitorar participação) | professor | `AUSENTE` | — |
| **Painel de controle / Suporte** | professor | `AUSENTE` | — |

---

## 5. Backlog priorizado

IDs no formato `ORION-C-nn` (C de conformidade), para não colidir com os IDs
antigos do `docs/BACKLOG.md`.

### P0 — decisões que destravam o resto

- `ORION-C-01` `BLOQUEADO` — Ratificar B1 a B5 com o Dr. Pio e registrar a
  decisão na seção 3. Nenhum item abaixo que dependa de B1–B5 deve ser
  iniciado antes.
- `ORION-C-02` `AUSENTE` — Unificar o desconto logístico cruzado. Hoje há duas
  implementações divergentes da mesma regra; a de `services/materias_primas.py`
  é a que segue a especificação. Remover a outra.

### P1 — regras de negócio divergentes da especificação

- `ORION-C-03` — Semear os 6 eventos do §8.4 com nome, tipo, impacto, frase
  indicativa e as probabilidades 15/20/20/15/15/15. Inclui campo novo
  `frase_indicativa` e migração.
- `ORION-C-04` — Substituir a probabilidade igual pelo sorteio ponderado pelas
  probabilidades fixas.
- `ORION-C-05` — Implementar os impactos específicos por evento (retenção de
  30% e 20% das entregas, +30% e −20% no custo de MP, +15% na demanda).
- `ORION-C-06` — Trocar o fator de marketing linear pela fórmula logarítmica do
  §14.1.1, com teto de +20% e saturação em R$ 10.000.
- `ORION-C-07` — Ranking multicritério com os 5 eixos e pesos do §12.4,
  incluindo o eixo de Sustentabilidade, que hoje não existe. Depende de B5
  para os desempates.
- `ORION-C-08` — Corrigir o custo do operador para R$ 1.800 e definir a
  conversão mês/rodada.
- `ORION-C-09` — Limite de expansão de +50% sobre as máquinas iniciais.
- `ORION-C-10` — Documentar ou corrigir a taxa de frete de produtos acabados
  (hoje R$ 0,10/km/unidade, sem origem documental).
- `ORION-C-11` — Validar número de rodadas entre 3 e 12.
- `ORION-C-12` — Restrição de investimento após duas rodadas de caixa negativo
  (RN-09).

### P2 — telas que faltam

- `ORION-C-13` — Tela de Encerramento da Rodada (template pronto).
- `ORION-C-14` — Relatórios Comparativos entre grupos (templates prontos).
- `ORION-C-15` — DRE e Fluxo de Caixa por grupo e rodada.
- `ORION-C-16` — Classificação final (template pronto).
- `ORION-C-17` — Ranking com destaques da rodada e evolução do grupo.
- `ORION-C-18` — Gerenciamento do jogo: monitoramento de participação por grupo.

### P3 — dívida e higiene

- `ORION-C-19` — Remover `homeold.html` (template órfão sem correspondência na
  especificação).
- `ORION-C-20` — Resolver `GameConfig.capacidade_maquina = 100`, um terceiro
  modelo de capacidade que não corresponde a nenhuma versão da spec.
- `ORION-C-21` — Decidir o destino de `services/vendas.py`, que implementa um
  modelo de demanda por grupo isolado, diferente e concorrente com a alocação
  competitiva de `fechar_rodadas.py`.
- `ORION-C-22` — Consertar a trilha principal de migrations, hoje inconsistente
  (`no such column: CONFIG.ranking_pesos`). Só `migrations_ci` sobe limpa.
- `ORION-C-23` — Cobrir `export_resultados_pdf` e `export_resultados_excel`
  com teste (52 linhas sem execução; CSV e JSON já têm).
- `ORION-C-24` — Cobrir `PainelGrupoView.post` (63 de 176 linhas sem execução).
- `ORION-C-25` — Subir a catraca dos gates: periférico de 60 para 70, núcleo de
  85 para 90.

---

## 6. Registro de 2026-09-18

Bugs corrigidos, todos com teste que falha sem a correção:

- Import quebrado em `sortear_eventos_rodada` (`sortear_eventos` → `sortear_evento`).
  O comando roda a cada minuto por `django_crontab` e falhava com `ImportError`
  em toda execução: o sorteio de eventos nunca acontecia.
- `/config/wizard/` respondia 500 em toda requisição — `Decimal` não serializa
  em JSON na sessão. O assistente nunca passou da etapa 1.
- `/grupos/novo/` respondia 500 em toda requisição — `GrupoCadastroForm`,
  `MembroFormSet` e `User` usados sem import, e o template não renderizava o
  formset. Não era possível criar equipe alguma.

Outros:

- Redesenho das telas em torno do trilho de rodada, com contagem regressiva.
- Relatórios financeiros como painel visual (KPIs com variação, composição de
  custo por origem, trajetória por rodada).
- `TIME_ZONE` de UTC para `America/Fortaleza`; `LANGUAGE_CODE` para `pt-br`.
- Gate de cobertura separado em núcleo (85%) e periférico (60%), porque
  `views.py` e `management/commands/*` estavam **fora da medição** — foi por
  isso que o import quebrado passou pelo CI.
- Smoke que entra em toda rota do `urlpatterns` como visitante, membro e
  professor, exigindo nenhum 5xx.

Estado da suíte ao final: **102 testes**, núcleo 91%, periférico 71%.

---

## 7. Como verificar

Sempre via Docker. Nunca criar venv local.

```bash
docker compose run --rm web python manage.py test app --settings=simulador_operacional.settings_test
```

Gates de cobertura, na mesma sequência do CI:

```bash
docker compose run --rm web sh -c "pip install -q coverage==7.6.1; coverage run --rcfile=../.coveragerc-critical manage.py test app --settings=simulador_operacional.settings_test && coverage report --rcfile=../.coveragerc-critical --fail-under=85 && coverage report --rcfile=../.coveragerc-perifericos --fail-under=60"
```

---

## 8. Documentos relacionados

| Documento | Papel |
|---|---|
| `_documentação/TXT/` | Especificação. Fonte da verdade. |
| `docs/GUIA_IMPLEMENTACAO.md` | Este arquivo. O que falta e em que ordem. |
| `docs/BACKLOG.md` | Histórico. Status não confiável — ver seção 1. |
| `SPRINTS.md` | Histórico. Desatualizado. |
| `docs/RELEASE_CHECKLIST.md` | Passos de release. Ativo. |
| `docs/RUNBOOK_OPERACAO.md` | Operação. Ativo. |
