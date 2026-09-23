# Guia de Implementação ORION

Documento único de referência para levar o simulador à conformidade com a
especificação. Substitui `SPRINTS.md` e `docs/BACKLOG.md` como fonte de
verdade sobre o que está feito — os dois continuam no repositório como
histórico, mas não devem ser consultados para decidir o que falta.

Última auditoria de prontidão: **2026-09-20** (RN-01/RN-02 e fluxo de primeira turma).
Ver `docs/AUDITORIA_REGRAS_INICIAIS.md`, `docs/BASE_REGIONAL.md` e `tasks/todo.md`
para evidências e limites desta verificação; as outras seções preservam o histórico.

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
| B1 | Composição dos produtos | §6.1: A = 120 kg MP1 + 40 MP2 + 60 MP3 + 80 MP4 | §13.2: A = 2 un MP1 + 1 un MP2 | Versão A | **§6.1** (2026-09-18) |
| B2 | Perecibilidade | §6.2: A não perece, B perece em 1 rodada, C não perece | §13.8: todos os produtos valem 2 rodadas | Versão A | **§6.2** (2026-09-18) |
| B3 | Capacidade de máquina | §13.4: 400 min por máquina por rodada | RN-06: turno único de 87 h = 5.220 min | Versão A (400) | **§13.4** (2026-09-18) |
| B4 | Eventos por rodada | §8.2: exatamente 1, probabilidades somam 100% | RN-10: até 2 simultâneos | Versão A (1) | **§8.2** (2026-09-18) |
| B5 | Critério de desempate | §12.5: EO → SD → DS → Receita bruta → alfabética | RN-12: lucro acumulado → market share → caixa → penalidades → alfabética | — | **§12.5** (2026-09-18, confiança baixa) |

### Critério usado nas decisões acima

Política do dono do projeto, 2026-09-18: **a documentação decide**. Onde há
duas versões escritas, vale a que é internamente consistente com o resto da
própria documentação. As evidências:

- **B1** — a composição em kg do §6.1 reproduz na vírgula os custos que o
  próprio §6.1 declara (A R$ 2.260,00 · B R$ 2.840,00 · C R$ 3.730,00). O
  §13.2 não tem tabela de custo que o sustente.
- **B2** — mesmo documento verificado em B1, e dá papéis distintos aos
  produtos: B exige produção sob demanda, A e C permitem estoque.
- **B3** — 400 min reproduzem exatamente as capacidades declaradas no §13.5
  (3.000 / 1.500 / 800 unidades). O RN-06 daria 13x mais e contradiria a
  tabela do próprio documento 13.
- **B4** — as probabilidades do §8.4 somam 100%, o que só fecha com sorteio
  único. "Até 2" exige outro modelo probabilístico.
- **B5** — **confiança baixa.** O único apoio é o documento 12 ser um dos dois
  únicos marcados "Pronto" no nome do arquivo; não há verificação aritmética.
  Reverter é barato se o autor da especificação decidir diferente.

### Extração legível da especificação

`_documentação/MD/` traz os 15 documentos reextraídos do `.docx` por script,
com as tabelas preservadas como tabelas — no `.txt` elas viravam texto
corrido ilegível (`CritérioSiglaPeso (P)Eficiência OperacionalEO0,30...`).

**23 imagens coladas** foram lidas e transcritas nos arquivos: as 11 fórmulas
do §12, o fator de marketing do §14, o DER do §4 e os mockups do §10. A fonte
de verdade continua sendo o `.docx`; a extração existe para o conteúdo ser
pesquisável e versionado.

Os mockups do §10 ficam como registro, não como direção de interface — a
decisão do dono do projeto é manter o layout atual.

Fora do §12, a recuperação trouxe uma fórmula que estava perdida:

```
Mc = 1 + 0,20 · ln(1 + Ic) / ln(1 + 10000)          §14.1.1
```

Esse é o fator de marketing do `ORION-C-06`, hoje implementado como modelo
linear. **Atenção:** a tabela de exemplo do próprio §14.1.3 não bate com a
fórmula — ela mostra Mc = 1,038 para Ic = 1.000, enquanto a fórmula dá 1,150.
Os valores intermediários da tabela seguem outra regra e só o teto de 20%
coincide. Vale conferir qual das duas vale antes de implementar.

### Fórmulas do §12, recuperadas das imagens do .docx

As fórmulas de classificação **não existem como texto em lugar nenhum**: no
`.docx` elas são 11 imagens PNG coladas, e por isso sumiram na conversão
para `.txt`, deixando linhas em branco onde deveriam estar. Foram lidas das
imagens e transcritas aqui, para não dependerem mais de abrir o Word.

```
Pontuação Total (%) = (EO × P₁) + (DF × P₂) + (EE × P₃) + (SD × P₄) + (DS × P₅)

EO = (Produção Líquida / Capacidade Utilizada) × F₁
   + (Produtos Vendidos / Produtos Disponíveis) × F₂
   + (1 − Perdas Totais / (MP + Produtos)) × F₃          F₁=0,4 F₂=0,4 F₃=0,2

DF = (IL × W₁) + (IR × W₂) + (IE × W₃)                    W₁=0,4 W₂=0,3 W₃=0,3
  IL = (Lucro Líquido / Receita Bruta) × 100
  IR = (Lucro Líquido / Ativos Totais Médios) × 100
  IE = (Custo das Vendas / Estoque Médio) × 100

EE = (Custo das Vendas / Estoque Médio Operacional) × 100
     Estoque Médio = (Estoque Inicial + Estoque Final) / 2

SD = (Σ vendidas / Σ demandas máximas) × 100   definida pelo PO, ver B8

DS = (DS₁ × S₁) + (DS₂ × S₂) + (DS₃ × S₃)                 S₁=0,5 S₂=0,3 S₃=0,2
  DS₁ = 1 − (Perdas Totais / (MP + Produtos))
  DS₂ = 1 − (Distância Média das Compras / Distância Máxima Teórica)
  DS₃ = (Produtos Enviados para praças ≤ 1.000 km) / Total Enviado
```

Pesos por eixo (§12.4): EO 0,30 · DF 0,25 · EE 0,15 · SD 0,20 · DS 0,10.

#### Problemas que a leitura das fórmulas revelou

- **B8 · SD não tinha fórmula no documento. `RESOLVIDO` em 23/09/2026 pelo
  Product Owner — ver a seção B8 adiante.**
  "Satisfação da Demanda" aparece **4 vezes em toda a especificação de 15
  documentos**, todas no doc 12, e todas são menção — nunca definição: a lista
  de eixos (§12.2), o título da seção (§12.3.4), a tabela de pesos (§12.4) e o
  desempate (§12.5). Não existe `12.3.5` em documento nenhum, nenhum outro
  documento cobre, e o `.docx` não tem notas de rodapé, comentários, caixas de
  texto nem alterações controladas — o corpo do documento é tudo o que há. A seção §12.3.4 se chama "Satisfação da
  Demanda (SD)", mas o corpo dela define **DS** (Sustentabilidade): a fórmula
  é `DS = (DS₁×S₁)+(DS₂×S₂)+(DS₃×S₃)` e os subcomponentes são redução de
  perdas, proximidade logística das compras e foco regional das entregas —
  todos indicadores ambientais, nenhum de atendimento de demanda. Parece erro
  de edição: o conteúdo de um §12.3.5 (Sustentabilidade) que nunca existiu
  foi colado dentro do §12.3.4. **Resultado: o eixo SD, que vale 0,20 — o
  segundo maior peso —, não tem definição.** Precisa ser criado.
- **B9 · EE contado duas vezes — `RESOLVIDO` (2026-09-23), era defeito nosso.**
  A leitura anterior ("a especificação conta o giro duas vezes") estava errada.
  O §12.3.2 nomeia `IE` de **Eficiência de Estoques (financeira)** sobre
  "Estoque Médio"; o §12.3.3 define `EE` como **eficiência logística
  operacional** sobre "Estoque Médio **Operacional**". São dois denominadores
  distintos, nomeados de propósito. Quem colapsou os dois num valor só foi a
  implementação, e aí o EE virou clone do IE — 24% da nota medindo a mesma
  coisa.
  Critério adotado: `IE` sobre o estoque total (MP + acabado, o ativo de
  estoque) e `EE` sobre o acabado, que é o que gira na operação comercial. O
  §7.4 e o §13.8 já tratam os dois estoques como coisas distintas, com custo de
  armazenagem próprio para cada um. `ConsolidadoRodadaGrupo` passa a guardar os
  dois valores, porque a média do §12.3.3 precisa da rodada anterior.
- **B10 · O limiar de 1.000 km em DS₃ perdeu sentido na base regional.** Com a
  sede em Currais Novos, a praça mais distante é Fortaleza, a 470 km. Todas as
  cidades cumprem o critério, então DS₃ = 1 sempre e o subindicador vira
  constante. O limiar precisa ser recalibrado para a nova geografia — algo
  como 200 km separaria o Seridó das capitais.
- **EE não é limitado a 100.** Sendo uma razão de giro, passa de 100 com
  facilidade — a própria tabela de exemplo do §12.6 traz EE de 110 e 105. A
  soma ponderada precisa saber lidar com isso.

### B8 · Fórmula de SD — `RATIFICADA` pelo Product Owner em 23/09/2026

O §12.3.4 traz **título e glosa do SD sobre a fórmula do DS**. Verificado na
imagem original (`word/media/image8.png`), não na conversão: a transcrição em
Markdown é fiel, o erro é de edição do documento. Como não existe §12.3.5, a
leitura coerente é que ali deveriam ser duas seções — a que sobrou é a do DS,
e a do SD se perdeu.

Confirmado pela própria tabela do §12.6, que dá valores **diferentes** para os
dois eixos (G1: SD 85, DS 92; G3 chega a inverter, SD 82 contra DS 75). Se
compartilhassem fórmula, as colunas seriam idênticas.

**A fórmula, definida pelo Dr. Pio:**

```
SD Local  = (Unidades vendidas na praça / Demanda máxima da praça) × 100
SD Global = (Σ unidades vendidas / Σ demandas máximas) × 100
```

somando os pares cidade × produto. A **SD Global** é a que pontua; a **SD
Local** alimenta o mapa de calor do painel, como apoio à decisão.

**Três pontos decididos junto com ele, e o porquê:**

| Ponto | Decisão | Razão |
|---|---|---|
| Vendidas ou entregues | **Vendidas** | O §9.2 limita a absorção à demanda. Com "entregues", despejar 5.000 numa praça de demanda 1.000 daria SD = 500%. E `entregue/disponível` já é o segundo termo do EO. |
| Denominador | **Todas as praças** | Quem opera concentrado não passa da fatia da sua cidade. A cobertura entra embutida, sem o segundo termo artificial que a fórmula anterior precisava. |
| Valor do denominador | **Calculado** | A proposta original trazia 64.000 fixo. A soma do §9.1 dá 66.000, e é *por produto* — com três produtos, 198.000. Na base regional, outro número. Fixo quebraria em silêncio. |

**Teto em 100:** marketing (§14.1) e o evento de boom (§8.4) elevam a demanda
no momento da venda, e o denominador aqui é a demanda catalogada. Sem o teto,
o eixo passaria de 100 por efeito de outro módulo.

**O que saiu:** a fórmula anterior (`profundidade × 0,6 + cobertura × 0,4`)
era invenção do projeto. O termo de cobertura dava **+40 pontos fixos** a quem
atendesse uma praça de uma praça ativa — bônus artificial que mascarava o
comportamento real dos outros eixos.

**Efeito colateral registrado:** com o bônus fora, o cenário de
`test_fechamento_distribui_demanda_por_preco` inverteu. O grupo que vendeu
mais (67 contra 33) vence em EO e SD, mas perde no DF, porque tem meio milhão
de caixa parado e o IR (ROA) do §12.3.2 pune ativo ocioso. É a fórmula do
documento funcionando; o teste deixou de comparar a pontuação total e passou a
comparar eixo a eixo.

**Atenção:** o campo `atendimento_demanda_percent` **não serve** para SD. Ele
calcula `vendidos / ofertados` — métrica de oferta, não de demanda, e
duplicata do segundo componente de EO. O nome engana.

### Critérios de desempate: existem, e são dois

A documentação **já traz** critérios, em dois lugares, ambos dizendo valer
para "empate na pontuação final":

| §12.5 (doc "Pronto") | RN-12 (doc "Semi-Pronto") |
|---|---|
| 1. Maior Eficiência Operacional | 1. Maior lucro acumulado |
| 2. Maior Satisfação da Demanda | 2. Maior market share médio |
| 3. Maior Desempenho em Sustentabilidade | 3. Maior saldo de caixa no fim |
| 4. Maior Receita Bruta | 4. Menor número de penalidades |
| 5. Ordem alfabética | 5. Ordem alfabética |

Decisão B5 mantida no **§12.5**, agora com três apoios em vez de um:

1. o documento 12 é um dos dois únicos marcados "Pronto" no nome do arquivo;
2. o §12.5 desempata pelos mesmos eixos que compõem a nota — quando a soma
   ponderada empata, vence quem foi melhor no eixo de maior prioridade. O
   RN-12 desempata por métricas que não entram na nota;
3. com a fórmula de DS recuperada, o critério 3 do §12.5 deixou de ser
   inimplementável.

O critério 2 do §12.5 depende de SD, que ganhou fórmula em 23/09/2026 (B8).
O desempate roda agora do critério 1 ao 5, sem pular nenhum.

### Quem decide o quê

O Dr. Pio Marinheiro é o Product Owner e autor da especificação. **O desenho
dele tem prioridade.** Onde a implementação se afasta do que ele escreveu, a
mudança não é definitiva até ele ratificar — mesmo quando a motivação é boa e
mesmo quando partiu de instrução do dono do projeto.

Três categorias, com dono diferente:

| Categoria | Quem decide | Exemplos |
|---|---|---|
| **A especificação se contradiz** | Dr. Pio | B1–B5: composição, perecibilidade, capacidade, eventos por rodada, desempate |
| **A especificação é omissa ou não fecha** | Dr. Pio | B10 (limiar de 1.000 km), frete de produto |
| **Contexto de aplicação da turma** | Rafael | D9.1–D9.3: sede, praças regionais, demanda por população |

**Pendências para o Dr. Pio, por ordem de impacto:**

1. **D11 · Variedade de eventos.** O §8.2 pede probabilidade constante; a
   redução de peso do evento recente a torna levemente dependente do
   histórico (até 1,3 p.p. de desvio). Atende ao pedido de variedade do dono
   do projeto, mas afasta-se da letra do documento.
2. **D9.5 · Custo do operador.** Ele escreveu R$ 1.800/mês; a rodada virou o
   período de competência da folha. Leitura, não transcrição.
3. **B10.** O limiar de 1.000 km em DS₃, que a base regional tornou inócuo.
   (B9 saiu desta lista: o §12 distingue IE de EE e a implementação é que
   havia colapsado os dois — corrigido em 2026-09-23.)

O que **não** precisa dele: correções de bug que não tocam regra de negócio
(imports quebrados, `Decimal` na sessão, fuso horário) e escolhas internas de
código (services, testes, unificação de duplicatas).

### D9 · Desvios deliberados da especificação

Decisões do dono do projeto que **contrariam a documentação de propósito**.
Ficam registradas aqui para ninguém as confundir com divergência acidental.

| # | Tema | O que a spec diz | O que vale | Motivo |
|---|---|---|---|---|
| D9.1 | Sede da fábrica | §9: Natal/RN | **Currais Novos/RN** | contexto real da turma |
| D9.2 | Praças de venda | §9.1: 10 capitais nacionais | **12 cidades da região** (Seridó, RN, PB, PE, CE) | idem |
| D9.3 | Demanda por praça | §9.1: tabela digitada | **derivada da população** pelo fator 0,207%, extraído da própria tabela do §9.1 | regra explícita e auditável no lugar de número por cidade |
| D9.4 | Fornecedores de MP | §7.1: cidades nacionais | **cidades da região**, cada MP com fornecedor perto e longe | preserva a escolha de fornecedor como decisão logística |
| D9.5 | Custo do operador por rodada | §14.2.4: R$ 1.800/mês + RN-06: rodada = 1 semana | **R$ 1.800 por rodada**, sem conversão por tempo | o professor define o prazo livremente; converter por tempo decorrido faria o custo da mesma decisão mudar conforme o prazo |
| D9.6 | Sigilo da rodada aberta | não previsto | **resultado só aparece após o fechamento** | é um jogo de competição; desempenho alheio antes da submissão muda a decisão de quem ainda não decidiu |
| D11 | Variedade de eventos | §8.2: "probabilidade **constante** de ocorrência" | **peso reduzido do evento recente** (×0,05 / ×0,30 / ×0,65), nunca bloqueio | bloquear achata os pesos: com 3 eventos de 60/30/10, cooldown duro os transforma em 33/33/33 |
| D10 | Unidade do frete | §7.2: R$ 1,50 por km **por kg** | **§7.2 literal: R$ 1,50 por km por kg** | a regra está expressa no documento e prevalece |

**Consequência de D9.2 e D9.3 no equilíbrio do jogo.** O mercado regional é
cerca de 5x menor que o nacional, e a capacidade produtiva não mudou:

| Cenário | Capacidade de A (5 grupos) | Demanda de A | Razão |
|---|---|---|---|
| Nacional (§9.1) | 15.000 | 33.000 | 0,45x — falta capacidade |
| Regional (D9.2) | 15.000 | 6.750 | 2,2x — sobra capacidade |

O recurso escasso deixa de ser produção e passa a ser demanda. Isso ativa a
curva de sensibilidade a preço e o investimento em marketing, que estavam
praticamente inertes enquanto a demanda superava a oferta. Se ficar punitivo
demais, o ajuste indicado é **reduzir as máquinas iniciais**, não inflar a
demanda — inflar quebraria a proporcionalidade com a população.

**D11 · Variedade de eventos sem falsear os pesos.** O cooldown original
bloqueava o evento das duas rodadas anteriores. Isso torna a probabilidade
dependente do histórico e, com poucos eventos, destrói a configuração do
professor: medido com 3 eventos de pesos 60/30/10, um cooldown duro de 2
rodadas os achata para **33/33/33**.

A solução é reduzir o peso do evento recente, nunca zerá-lo — ele continua
possível, só fica improvável. Medido em 3.000 rodadas com os 6 eventos do
§8.4:

| | Sem ajuste | Cooldown duro de 2 | **Peso reduzido** |
|---|---|---|---|
| Repetição consecutiva | 16,9% | 0% | **1,2%** |
| Repetição em 3 rodadas | 42,7% | 25,5% | **23,8%** |
| Desvio máximo dos pesos | 0,1 p.p. | 1,5 p.p. | **1,3 p.p.** |

O peso reduzido ganha do cooldown duro na variedade **e** na fidelidade aos
pesos, e degrada com elegância quando há poucos eventos configurados. Os
multiplicadores estão em `PENALIDADE_EVENTO_RECENTE`.

**Frete de produto acabado** também usa o caminhão. Correção de uma
afirmação errada da auditoria de 2026-09-18: dizia que a distribuição não
cobrava frete nenhum. Ela cobrava — inline em `views.py`, com a taxa de
R$ 0,10/km/unidade. O erro veio de procurar o cálculo em `fechar_rodadas.py`
e no `economia_service`, quando ele estava na view.

O problema real era outro: a taxa não tinha origem documental e era
**linear**, então sair de 40 para 41 unidades mudava o frete em 2% e não
havia lição de planejamento de carga. Com o caminhão, dobra:

| Envio para Natal (172 km) | Frete antigo | Frete novo |
|---|---|---|
| 40 unidades de A (1 caminhão cheio) | R$ 688,00 | R$ 1.360,00 |
| 41 unidades de A (2 caminhões, 51%) | R$ 705,20 | **R$ 2.720,00** |

A mensagem de confirmação passa a dizer quantas viagens e qual a ocupação.

As distâncias e populações da tabela regional são aproximadas e devem ser
conferidas contra IBGE e rota real antes do uso em sala (`ORION-C-27`).

Consequências já mapeadas das decisões:

- **B3** tinha o parâmetro legado `capacidade_maquina = 100`, que não
  correspondia a nenhuma versão e não entrava no cálculo real. Foi removido
  (`ORION-C-20`).
- **B4** mantém o "até 2 eventos" como evolução futura (Sprint 29), com modelo
  probabilístico próprio.
- **B5** não está implementado como descrito em nenhuma das versões; exige os
  5 eixos do §12.2 (`ORION-C-07`).

---

## 4. Matriz de conformidade

> `CONFORME` significa código validado pela suíte automatizada. A suíte
> reconstruída passou com 232 testes em 2026-09-19.

### 4.1 Cadastro, acesso e configuração

| Regra | Origem | Status | Onde |
|---|---|---|---|
| Perfis aluno / CEO / professor | RF.01 | `CONFORME` | `models.User.tipo_usuario` |
| CEO por rodada, só ele submete | RF.01, RN-03 | `CONFORME` | `models.CEOGrupoRodada`, `PainelGrupoView` |
| Auditoria de submissão (usuário, data/hora, IP) | RF.01 | `CONFORME` | `models.AuditoriaSubmissaoRodada` |
| Grupo com 3 a 6 participantes | RN-02 | `CONFORME` | `forms.MembroFormSet` (`min_num=3`, `max_num=6`) |
| Capital inicial R$ 1.000.000 | RN-02 | `CONFORME` | `GameConfig.capital_inicial` |
| 40 máquinas iniciais (15 A / 15 B / 10 C) | RN-02 | `CONFORME` | `views.CAPACIDADE_PADRAO_POR_CODIGO` |
| 80 funcionários iniciais (2 por máquina) | RN-02 | `CONFORME` | `garantir_capacidades_grupo`, `test_primeira_turma` (padrões iniciais) |
| Senha mínima de 8 caracteres com letras e números | RN-01 | `CONFORME` | `LetterAndDigitPasswordValidator`, também aplicado em `MembroForm` |
| Número de rodadas entre 3 e 12 | RN-02 | `CONFORME` | `GameConfig`/`GameConfigForm`, `test_regras_iniciais`; limite da rodada usa o jogo selecionado |

### 4.2 Produção

| Regra | Origem | Status | Onde |
|---|---|---|---|
| Máquinas dedicadas por linha, sem compartilhar | §13.4 | `CONFORME` | `CapacidadeProdutoGrupo` |
| Tempo por unidade: A 2 min, B 4 min, C 5 min | §13.3 | `CONFORME` | seed `produtos` |
| Máquina sem 2 operadores não produz | §14.3, RN-06 | `CONFORME` | `capacidade_unidades_rodada`: `min(maquinas, operadores // 2)` |
| Produção parcial quando falta MP ou tempo | §13.7 | `CONFORME` | `fechar_rodadas` |
| Só unidades inteiras | §6.3 | `CONFORME` | `int(minutos_total // tempo)` |
| Custo de produção = MP consumida | §13.9 | `CONFORME` | `services/producao.py` |
| Capacidade por máquina: 400 min | §13.4 (decidido B3) | `CONFORME` | `CapacidadeProdutoGrupo.minutos_por_maquina = 400` |

### 4.3 Matéria-prima e logística

| Regra | Origem | Status | Onde |
|---|---|---|---|
| 4 MPs com preços 3,00 / 5,50 / 8,00 / 15,00 | §7.1 | `CONFORME` | seed `materias_primas` |
| Recebimento na rodada seguinte (D+1) | §7.2 | `CONFORME` | `CompraMateriaPrima.rodada_pedido` |
| Frete de MP a R$ 1,50/km por kg adquirido | §7.2 | `CONFORME` | `services/logistica.calcular_frete_materia_prima` |
| Armazenagem de MP a 2% do valor de compra | §7.4 | `CONFORME` | `fechar_rodadas` |
| Fornecedores por cidade | §7.1 | `CONFORME` | `views.MATERIA_PRIMA_FORNECEDORES` |
| Desconto logístico cruzado de R$ 0,50/km por produto remetido | §7.2.1 | `CONFORME` | `services/logistica.calcular_frete_materia_prima` |
| Frete de produtos acabados | §9.2a + decisão de calibração | `CONFORME` | R$ 5,00/km + R$ 500,00 de carga/descarga por viagem em `services/logistica.calcular_frete` |

### 4.4 Comercialização e demanda

| Regra | Origem | Status | Onde |
|---|---|---|---|
| 12 cidades regionais com distância e demanda derivada | §9.1 + D9.1–D9.3 | `CONFORME` | `seed_dados_base`, `test_base_regional`; fontes e data em `docs/BASE_REGIONAL.md` |
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
| Fator de marketing: `Mc = 1 + 0,20 · ln(1+Ic) / ln(1+10000)` | §14.1.1 | `CONFORME` | `services.marketing.fator_de_investimento`, com teto de R$ 10.000 e testes de curva, teto e retorno marginal em `test_marketing` |
| Salário do operador R$ 1.800/mês | §14.2.4, §14.3 | `CONFORME` | `CUSTO_OPERADOR_POR_RODADA`: cada rodada fecha uma folha integral, sem pró-rata de calendário |
| Custo da máquina R$ 8.000 | §14.2.4 | `NAO_VERIFICADO` | — |
| Limite de expansão de +50% sobre as máquinas iniciais | §14.2.1 | `CONFORME` | `services.investimentos.limite_de_expansao` bloqueia compras acima do teto, inclusive pendentes; `test_regras_investimento` |

### 4.6 Eventos aleatórios

| Regra | Origem | Status | Onde |
|---|---|---|---|
| Sorteio automático por rodada | §8.2 | `CONFORME` | `services/eventos.py` + comando agendado; isolamento por jogo e idempotência em `SortearEventosRodadaCommandTest` (20/09/2026) |
| Evento aplicado igualmente a todos os grupos | §8.2 | `CONFORME` | `EventoRodada` por rodada |
| Os 6 eventos nomeados do §8.4 | §8.4 | `CONFORME` | `seed_dados_base` |
| Probabilidades 15 / 20 / 20 / 15 / 15 / 15 | §8.4 | `CONFORME` | `seed_dados_base` + sorteio ponderado em `services/eventos.py` |
| Impactos específicos por evento (ex.: greve retém 30% das entregas) | §8.4 | `CONFORME` | `services/retencao.py` + `Evento.retencao_entregas_percent` |
| Frase indicativa por evento | §8.5 | `CONFORME` | `Evento.frase_indicativa`, exibida no boletim |
| Até 2 eventos simultâneos | RN-10 | `AUSENTE` | decidido B4: 1 por rodada. "Até 2" fica como Sprint 29 |

### 4.7 Fechamento, financeiro e ranking

| Regra | Origem | Status | Onde |
|---|---|---|---|
| Fechamento automático no prazo | §11.1 | `DIVERGENTE` | O painel bloqueia decisões ao vencer o prazo; o serviço local consulta `fechar_rodadas` a cada 1 s, além da duração do comando. Não há garantia do instante exato exigido pelo DOCX 11, mas a janela técnica foi reduzida. Transação por rodada e retomada após falha verificadas em `FechamentoRecuperacaoTest` (20/09/2026). Ensaio HTTP isolado de migração, seed e rodada vencida concluído em 21/09/2026; validar a tolerância na rede da instituição antes da aula. |
| Bloqueio de edição após o prazo | §11.1 | `CONFORME` | `permite_edicao` |
| Penalidade de 10% por não submeter | §11.2, RN-04 | `CONFORME` | `fechar_rodadas.caixa_base_para_penalidade` usa o saldo de caixa da rodada anterior; na primeira rodada usa o capital inicial. Protegido por `FechamentoRodadaPenalidadeTest`. |
| Decisões omitidas repetem a rodada anterior | §11.2 | `CONFORME` | `services/fechamento.py` |
| Consolidado persistido por grupo e rodada | §11.3d | `CONFORME` | `ConsolidadoRodadaGrupo` |
| Ranking multicritério de 5 eixos (EO, DF, EE, SD, DS) | §12.2 | `CONFORME` | `services/pontuacao.py` |
| Pesos 0,30 / 0,25 / 0,15 / 0,20 / 0,10 | §12.4 | `CONFORME` | `parametros.PESOS_EIXOS`, ajustáveis por `GameConfig.ranking_pesos` |
| Critérios de desempate | §12.5 (decidido B5) | `CONFORME` | `pontuacao.ordenar_classificacao`, aplicado em `RankingView` |
| Restrição de investimento após 2 rodadas de caixa negativo | RN-09 | `CONFORME` | `investimentos.impedimento_para_investir` |

### 4.8 Telas (§10)

| Tela | Perfil | Status | Rota |
|---|---|---|---|
| Inicial | todos | `CONFORME` | `/` |
| Login | todos | `CONFORME` | `/login/` |
| Painel do grupo | CEO, membro | `CONFORME` | `/painel/` |
| Decisões por rodada | CEO | `CONFORME` | integrado ao painel |
| Relatórios financeiros | todos | `CONFORME` | `/relatorios/` — DRE e Fluxo de Caixa via `services/dre.py` |
| Configuração do jogo | professor | `CONFORME` | `/config/`, `/config/wizard/` |
| Abrir rodada | professor | `CONFORME` | `/abrir_rodada/` |
| Grupos | professor | `CONFORME` | `/grupos/` |
| Ranking | todos | `CONFORME` | `/ranking/` — classificação, destaques da rodada e evolução do grupo |
| Ajuda | todos | `CONFORME` | `/ajuda/` |
| **Encerramento da rodada** | CEO | `CONFORME` | `/encerramento/`, `EncerramentoRodadaView` |
| **Relatórios comparativos** | todos | `CONFORME` | `/relatorios/comparativos/`, `RelatoriosComparativosView` |
| **Classificação final** | todos | `CONFORME` | `/classificacao/`, `ClassificacaoFinalView` |
| **Gerenciamento do jogo** (monitorar participação) | professor | `CONFORME` | `/gerenciamento/` |
| **Painel de controle / Suporte** | professor | `CONFORME` | `/gerenciamento/`, `GerenciamentoJogoView`; execução e falhas de jobs em `/jobs/` |

---

## 5. Backlog priorizado

IDs no formato `ORION-C-nn` (C de conformidade), para não colidir com os IDs
antigos do `docs/BACKLOG.md`.

### P0 — decisões que destravam o resto

- `ORION-C-01` `CONCLUIDO` (2026-09-18) — B1 a B5 decididos pela política "a
  documentação decide"; ver seção 3. **B5 tem confiança baixa** e vale ratificar
  com o Dr. Pio.
- `ORION-C-26` `CONCLUIDO` (2026-09-19) — B7 foi resolvido pela regra explícita
  do §7.2: R$ 1,50/km por kg adquirido. O §7.2.1 reduz R$ 0,50/km por produto
  remetido para a mesma cidade, limitado à quantidade adquirida.
- `ORION-C-02` `CONCLUIDO` (2026-09-19) — Removido o cálculo legado paralelo.
  O desconto cruzado é calculado apenas em `services/logistica.py`, com as
  quantidades e os valores definidos no §7.2.1.

### P1 — regras de negócio divergentes da especificação

- `ORION-C-03` `CONCLUIDO` (2026-09-18) — Semear os 6 eventos do §8.4 com nome, tipo, impacto, frase
  indicativa e as probabilidades 15/20/20/15/15/15. Inclui campo novo
  `frase_indicativa` e migração.
- `ORION-C-04` `CONCLUIDO` (2026-09-18) — Substituir a probabilidade igual pelo sorteio ponderado pelas
  probabilidades fixas.
- `ORION-C-05` `CONCLUIDO` (2026-09-18) — Retenção de entregas em
  `services/retencao.py`. Os impactos percentuais (custo de MP, custo
  logístico, demanda) já existiam; o que faltava era a retenção, e ela estava
  modelada como **queda de demanda na cidade** — a carga chegava, o mercado é
  que comprava menos, e na rodada seguinte não voltava nada. Agora a entrega é
  de fato retida: reaparece como envio da rodada seguinte sem cobrar frete de
  novo (o caminhão já saiu), e o perecível retido é perdido, como o §8.4 manda.
  Vale também para matéria-prima.
  `Evento` ganhou `retencao_entregas_percent` porque a greve tem **dois**
  efeitos (+30% no custo logístico *e* 30% retido) e `impacto_percentual`
  só comporta um.
- `ORION-C-06` `CONCLUIDO` (2026-09-18) — Fator de marketing logarítmico do
  §14.1.1 em `services/marketing.py`, com teto de +20% e saturação em
  R$ 10.000. A curva linear anterior estava duplicada em `views.py` e em
  `fechar_rodadas.py` e era inerte: o teto documental (R$ 10.000) rendia 1,02.
  A tabela de exemplo do §14.1.3 **não** reproduz a fórmula (declara 1,038 onde
  a fórmula dá 1,150, e salta de 1,051 para 1,200 entre R$ 5.000 e R$ 10.000,
  degrau que nenhuma curva logarítmica produz); vale a fórmula, que é contínua
  e bate nos dois extremos declarados.
- `ORION-C-07` `CONCLUIDO` (2026-09-18) — Ranking multicritério dos 5 eixos em
  `services/pontuacao.py`, com os pesos do §12.4 e o desempate do §12.5. O
  score anterior combinava quatro métricas que não existem em documento algum
  e Sustentabilidade não era calculada em lugar nenhum. `RankingView` passou a
  ler `ConsolidadoRodadaGrupo`, que é onde os eixos e a receita bruta vivem —
  sem eles não há como aplicar o desempate. A tabela de exemplo do §12.6 não
  reproduz a fórmula do §12.2 com os pesos do §12.4 (G1 daria 77,9 e a tabela
  declara 75,35); vale a parte normativa, fórmula e pesos.
- `ORION-C-08` `CONCLUIDO` (2026-09-19) — Custo do operador em R$ 1.800 por
  rodada; a rodada é o período de competência da folha, sem pró-rata de
  calendário, pois o professor define livremente o seu prazo.
- `ORION-C-09` `CONCLUIDO` (2026-09-18) — Teto de +50% sobre o parque inicial
  (§14.2.1), em `services/investimentos.py`. O limite é sobre o parque do
  grupo, não por linha de produto — o §14.2.1 justifica o teto por "restrições
  físicas do espaço industrial", e o que acaba é o galpão. Compra ainda não
  processada já consome o limite, senão bastava parcelar para furá-lo. O painel
  mostra quanto resta.
- `ORION-C-10` `CONCLUIDO` (2026-09-19) — Produto acabado cobra R$ 5,00/km
  mais R$ 500,00 de carga e descarga por viagem de até 12.000 kg. A calibração
  arredonda a referência de carga geral da ANTT para preservar a imersão e
  fazer distância e consolidação de carga influenciarem a competição.
- `ORION-C-11` `CONCLUIDO` — `GameConfig.numero_rodadas` já carrega
  `MinValueValidator(3)` e `MaxValueValidator(12)`, e o formulário de
  configuração é `ModelForm`, então a validação roda. Item era falso alarme.
- `ORION-C-12` `CONCLUIDO` (2026-09-18) — RN-09 em
  `services/investimentos.py`: dois fechamentos consecutivos com caixa
  negativo bloqueiam novos investimentos. **Resgate de aplicação financeira
  fica de fora** — é justamente o caminho de quem precisa de caixa, e a regra
  restringe investir, não desinvestir.

### P2 — telas que faltam

- `ORION-C-13` `CONCLUIDO` (2026-09-19) — Tela de Encerramento da Rodada em
  `/encerramento/`, com o resultado da última rodada fechada do próprio grupo.
- `ORION-C-14` `CONCLUIDO` (2026-09-19) — Relatórios Comparativos em
  `/relatorios/comparativos/`, com gráficos de desempenho e escopo isolado
  por jogo.
- `ORION-C-15` `CONCLUIDO` (2026-09-18) — DRE e Fluxo de Caixa em
  `services/dre.py`, apresentados na própria tela de Relatórios Financeiros,
  como o §10.3 descreve (uma tela, não duas). Os dois fecham: o DRE soma
  exatamente o lucro gravado e cada linha do fluxo soma exatamente o saldo
  gravado. A linha "Compras e investimentos" é o resíduo entre o caixa e o
  resultado — é ela que mostra ao aluno para onde o dinheiro foi antes de
  virar receita.
- `ORION-C-16` `CONCLUIDO` (2026-09-19) — Classificação final em
  `/classificacao/`, liberada após todas as rodadas configuradas fecharem.
  Soma os cinco eixos e a receita do ciclo e aplica o desempate do §12.5.
- `ORION-C-17` `CONCLUIDO` (2026-09-19) — Ranking em `/ranking/` exibe o
  líder, o maior lucro e a maior participação de mercado da rodada, além do
  histórico de posição e pontuação do grupo do usuário em cada rodada fechada.
- `ORION-C-18` `CONCLUIDO` (2026-09-19) — Gerenciamento em `/gerenciamento/`
  lista, por rodada aberta, o CEO, o estado da submissão e o horário de envio
  de cada grupo.

### P3 — dívida e higiene

- `ORION-C-19` `CONCLUIDO` (2026-09-19) — Removido `homeold.html`, template
  órfão sem rota, referência no código ou correspondência na especificação.
- `ORION-C-20` `CONCLUIDO` (2026-09-19) — Removido o parâmetro legado
  `capacidade_maquina = 100`, inclusive da migração consolidada; a capacidade
  efetiva permanece 400 minutos por máquina e produto, conforme §13.4 e decisão B3.
- `ORION-C-21` `CONCLUIDO` (2026-09-19) — Removido `services/vendas.py` e seu
  teste isolado: contrariavam a alocação competitiva entre grupos definida na
  §9.2(c) e já implementada em `fechar_rodadas.py`.
- `ORION-C-22` `CONCLUIDO` (2026-09-19) — A aplicação passou a usar por padrão
  a trilha consolidada `migrations_ci`, que sobe limpa. A sequência antiga em
  `migrations/` permanece apenas como histórico e não é mais executada.
- `ORION-C-23` `CONCLUIDO` (2026-09-18, verificado em 19/09) — Cobrir `export_resultados_pdf` e `export_resultados_excel`
  com teste (52 linhas sem execução; CSV e JSON já têm).
- `ORION-C-24` `CONCLUIDO` (2026-09-18, revalidado em 21/09) — Cobrir `PainelGrupoView.post` (63 de 176 linhas sem execução). `test_evento_estado_bloqueia_producao` protege o bloqueio por evento de estado e `test_evento_de_custo_de_transporte_encarece_o_frete` protege o multiplicador percentual do frete.
- `ORION-C-25` `CONCLUIDO` (2026-09-19) — Gates elevados: núcleo de 85 para
  90 e periférico de 60 para 70. A medição de 239 testes alcançou 92% e 81%,
  respectivamente.

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

### Sessão seguinte — classificação, marketing e relatórios contábeis

- `ORION-C-07`: os cinco eixos do §12 (`services/pontuacao.py`), com os pesos
  do §12.4 e o desempate do §12.5. `ConsolidadoRodadaGrupo` ganhou
  `eo/df/sd/ds_percent` e `valor_estoques`; `eficiencia_estoque_percent` passou
  a guardar o EE documentado em vez de uma métrica caseira.
- `ORION-C-06`: fator de marketing logarítmico, única implementação para a
  tela do aluno e para o fechamento.
- `ORION-C-15`: DRE e Fluxo de Caixa na tela de Relatórios Financeiros.
- `default_ranking_pesos` passou a devolver os cinco eixos; as quatro chaves
  antigas não correspondiam a nada da especificação.
- `ORION-C-09` e `ORION-C-12`: teto de expansão do parque e bloqueio de
  investimento por caixa negativo, as duas regras que existiam na
  especificação e em lugar nenhum do código.
- `ORION-C-05`: retenção de entregas de verdade, no lugar do corte de demanda
  que fingia representá-la.
- `ORION-C-23` e `ORION-C-24`: cobertura de `export_resultados_pdf`/`excel` e
  dos caminhos de erro de `PainelGrupoView.post` (capital, estoque e escopo),
  do bloqueio de produção por evento de estado e do multiplicador percentual
  do frete por evento.

Duas decisões que ficaram registradas como divergência, não como erro: as
tabelas de exemplo do §12.6 e do §14.1.3 não reproduzem as próprias fórmulas
que ilustram. Em ambos os casos vale a fórmula.

Verificação (2026-09-19): o Docker voltou e a suíte inteira rodou — **232
testes, todos OK**, sem nenhuma regressão. As três apostas de onde quebraria
(retenção de entregas, `RankingView`, tuplas do seed) estavam erradas. Gates:
núcleo passou o 85%, periférico em 79%.

Ponto em aberto para o Rafael: grupo que não opera na rodada tira DS = 80 e
EO = 20, porque "não teve perdas" e "não comprou longe" são verdade quando não
houve operação. É a fórmula do §12.3 ao pé da letra. Se isso for exploração
indevida, o caminho é zerar os eixos sem atividade.

---

## 7. Como verificar

Sempre via Docker. Nunca criar venv local.

```bash
docker compose run --rm web python manage.py test app --settings=simulador_operacional.settings_test
```

Gates de cobertura, na mesma sequência do CI:

```bash
docker compose run --rm web sh -c "pip install -q coverage==7.6.1; coverage run --rcfile=../.coveragerc-critical manage.py test app --settings=simulador_operacional.settings_test && coverage report --rcfile=../.coveragerc-critical --fail-under=90 && coverage report --rcfile=../.coveragerc-perifericos --fail-under=70"
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

## 9. Prontidão técnica — 20/09/2026

- População das 12 praças: Censo 2022/IBGE com malha 2023; distâncias
  rodoviárias com fontes e consulta registradas. Atualizações no seed
  e demanda derivada preservam D9.1–D9.3.
- Cadastro: e-mails distintos, exatamente um líder, 3–6 participantes e
  transação sem contas órfãs. Os recursos iniciais vêm do jogo selecionado.
- API administrativa: aluno/CEO não podem alterar configurações, catálogo,
  rodadas ou registros por operações de escrita. Decisões seguem pelo painel.
- Configuração: cinco eixos EO/DF/EE/SD/DS na tela e no seed; o fechamento usa
  os pesos do jogo. Não se convertem pesos antigos silenciosamente.
- Migração consolidada não cria mais administrador com senha fixa. Conta
  recém-provisionada neste banco teve senha invalidada; redefinição é interativa.
- Ensaio completo: duas equipes, três rodadas, D+1, produção, distribuição,
  submissão exclusiva, auditoria, sigilo nas telas, resultados e classificação.
- Verificação: **248 testes OK**, cobertura núcleo **93%**, periférico **85%**;
  migrações reais e seed repetido validados em banco temporário sem usuários.
- Operação: roteiro da primeira turma e Compose local com banco persistente
  e processamento periódico. O responsável ainda precisa definir a senha do
  professor e ensaiar navegador/rede/prazo antes da turma.

Esta evidência permite iniciar um ensaio funcional acompanhado com os padrões
RN-02. Não certifica nota pedagógica, carga, customização da planta ou publicação
em produção. As decisões pendentes e tarefas posteriores estão em `tasks/todo.md`.
