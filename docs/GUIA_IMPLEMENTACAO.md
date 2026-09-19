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

SD = SEM FÓRMULA NO DOCUMENTO  (ver B8)

DS = (DS₁ × S₁) + (DS₂ × S₂) + (DS₃ × S₃)                 S₁=0,5 S₂=0,3 S₃=0,2
  DS₁ = 1 − (Perdas Totais / (MP + Produtos))
  DS₂ = 1 − (Distância Média das Compras / Distância Máxima Teórica)
  DS₃ = (Produtos Enviados para praças ≤ 1.000 km) / Total Enviado
```

Pesos por eixo (§12.4): EO 0,30 · DF 0,25 · EE 0,15 · SD 0,20 · DS 0,10.

#### Problemas que a leitura das fórmulas revelou

- **B8 · SD não tem fórmula. Verificado na fonte, não na conversão.**
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
- **B9 · EE é contado duas vezes.** `IE = Custo das Vendas / Estoque Médio`
  (dentro de DF, peso 0,3 × 0,25 = 7,5%) e `EE = Custo das Vendas / Estoque
  Médio Operacional` (eixo próprio, 15%) são praticamente a mesma razão. Cerca
  de 22,5% da nota final mede giro de estoque. Pode ser intencional, mas vale
  ratificar.
- **B10 · O limiar de 1.000 km em DS₃ perdeu sentido na base regional.** Com a
  sede em Currais Novos, a praça mais distante é Fortaleza, a 470 km. Todas as
  cidades cumprem o critério, então DS₃ = 1 sempre e o subindicador vira
  constante. O limiar precisa ser recalibrado para a nova geografia — algo
  como 200 km separaria o Seridó das capitais.
- **EE não é limitado a 100.** Sendo uma razão de giro, passa de 100 com
  facilidade — a própria tabela de exemplo do §12.6 traz EE de 110 e 105. A
  soma ponderada precisa saber lidar com isso.

### B8 · Fórmula proposta para SD — aguardando ratificação

O eixo vale 0,20, o segundo maior peso, e não pode ficar indefinido. A
proposta abaixo parte da única frase que o documento oferece sobre ele —
"avalia o grau de atendimento ao mercado nas praças-alvo" (§12.3.4) — e evita
sobreposição com os outros quatro eixos.

```
SD = (SD₁ × T₁) + (SD₂ × T₂)                             T₁ = 0,6  T₂ = 0,4

SD₁ = Produtos Vendidos / Demanda Potencial das praças ativas
      quanto do mercado disponível a equipe capturou

SD₂ = Praças Atendidas / Praças Ativas
      em quantos mercados a equipe se fez presente
```

Por que só dois componentes, e não três como nos demais eixos: qualquer
terceiro candidato colide com um eixo existente. "Vendido / Enviado" é o
segundo componente de EO. "Sobra / Enviado" é o mesmo, invertido. Giro de
estoque já aparece duas vezes (B9). Padronizar a forma ao custo de medir a
mesma coisa três vezes seria pior que a assimetria.

**SD₂ é o que dá caráter próprio ao eixo:** pune concentrar tudo na praça
mais rentável e ignorar o resto do mercado — decisão que hoje não tem
consequência nenhuma na nota.

**Atenção ao implementar:** o campo `atendimento_demanda_percent` que existe
hoje **não serve** para SD. Ele calcula `vendidos / ofertados`, isto é, se o
que a equipe enviou vendeu — métrica de oferta, não de demanda, e duplicata
do segundo componente de EO. O nome engana.

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

**Mas o critério 2 do §12.5 depende de SD, que não tem fórmula (B8).** Até
isso ser resolvido, o desempate só roda do critério 1 ao 5 pulando o 2.

### Quem decide o quê

O Dr. Pio Marinheiro é o Product Owner e autor da especificação. **O desenho
dele tem prioridade.** Onde a implementação se afasta do que ele escreveu, a
mudança não é definitiva até ele ratificar — mesmo quando a motivação é boa e
mesmo quando partiu de instrução do dono do projeto.

Três categorias, com dono diferente:

| Categoria | Quem decide | Exemplos |
|---|---|---|
| **A especificação se contradiz** | Dr. Pio | B1–B5: composição, perecibilidade, capacidade, eventos por rodada, desempate |
| **A especificação é omissa ou não fecha** | Dr. Pio | B8 (SD sem fórmula), B9 (giro duplo), B10 (limiar de 1.000 km), frete de produto |
| **Contexto de aplicação da turma** | Rafael | D9.1–D9.3: sede, praças regionais, demanda por população |

**Pendências para o Dr. Pio, por ordem de impacto:**

1. **D10 · Unidade do frete.** O §7.2 diz R$ 1,50 por km **por kg**. Os valores
   dele foram preservados; só a unidade passou a ser por viagem de caminhão.
   Motivo: no exemplo do próprio §7.2.1, 500 kg de MP3 valendo R$ 4.000 geram
   R$ 750.000 de frete — 188x a carga, 75% do capital inicial numa compra. É
   aritmética, não preferência. **Mas a correção é uma leitura minha da
   intenção dele, e ele pode ter pensado outra coisa.**
2. **B8 · Fórmula de SD.** A proposta registrada é invenção minha, não dele.
   Vale 0,20 da nota. Não deve ser implementada sem ratificação.
3. **D11 · Variedade de eventos.** O §8.2 pede probabilidade constante; a
   redução de peso do evento recente a torna levemente dependente do
   histórico (até 1,3 p.p. de desvio). Atende ao pedido de variedade do dono
   do projeto, mas afasta-se da letra do documento.
4. **D9.5 · Custo do operador.** Ele escreveu R$ 1.800/mês; a rodada virou o
   período de competência da folha. Leitura, não transcrição.
5. **B9 e B10.** Giro de estoque contado duas vezes e o limiar de 1.000 km,
   que a base regional tornou inócuo.

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
| D10 | Unidade do frete | §7.2: R$ 1,50 por km **por kg** | **R$ 1,50 por km por viagem de caminhão** (12.000 kg) | a unidade do documento faz o frete valer 188x a carga; o jogo trava na primeira compra |

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

**D10 · O modelo de frete e o que ele ensina.** O caminhão é indivisível, e é
daí que vem a lição. Pedido de MP1 vindo de Mossoró (190 km):

| Pedido | Viagens | Ocupação | Frete | Frete / carga |
|---|---|---|---|---|
| 500 kg | 1 | 4% | R$ 285,00 | **19,0%** |
| 6.000 kg | 1 | 50% | R$ 285,00 | 1,6% |
| 12.000 kg | 1 | 100% | R$ 285,00 | **0,8%** |
| 12.001 kg | 2 | 50% | R$ 570,00 | 1,6% |

O frete de 500 kg e o de 12.000 kg é o mesmo: 24x de diferença no custo por
quilo, só por consolidar. Pedir 1 kg além do caminhão dobra a conta. A
distância continua pesando, mas sem dominar: o mesmo pedido cheio custa 0,3%
da carga vindo de Caicó e 2,0% vindo de Fortaleza.

O desconto do §7.2.1 vira frete de retorno: as viagens que levaram produto
para aquela cidade podem voltar carregadas com a matéria-prima, limitado
pelas viagens de produto que de fato existiram.

A taxa de ocupação volta no resultado para o aluno ver quanto de caminhão
vazio pagou — é ela, não o valor absoluto, que carrega a lição.

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
| 40 unidades de A (1 caminhão cheio) | R$ 688,00 | R$ 258,00 |
| 41 unidades de A (2 caminhões, 51%) | R$ 705,20 | **R$ 516,00** |

A mensagem de confirmação passa a dizer quantas viagens e qual a ocupação.

As distâncias e populações da tabela regional são aproximadas e devem ser
conferidas contra IBGE e rota real antes do uso em sala (`ORION-C-27`).

### Ainda bloqueado

- **B6 · Frete de produtos acabados.** A documentação é **silenciosa** sobre a
  taxa. A política "a documentação decide" não produz um número onde não há
  número. O código usa R$ 0,10/km/unidade, sem origem documental.
- **B7 · Unidade do frete de matéria-prima.** O §7.2.1 está aritmeticamente
  correto, mas economicamente impraticável: no exemplo do próprio documento,
  500 kg de MP3 valendo R$ 4.000 geram frete de R$ 750.000 — 188x o valor da
  carga e 75% do capital inicial numa única compra. Implementar como está
  escrito trava o jogo na primeira rodada. A fórmula R$ 1,50/km × kg parece ter
  sido pensada por lote, não por quilo-quilômetro. Precisa de decisão do autor
  da especificação.

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
| Capacidade por máquina: 400 min | §13.4 (decidido B3) | `CONFORME` | `CapacidadeProdutoGrupo.minutos_por_maquina = 400` |

### 4.3 Matéria-prima e logística

| Regra | Origem | Status | Onde |
|---|---|---|---|
| 4 MPs com preços 3,00 / 5,50 / 8,00 / 15,00 | §7.1 | `CONFORME` | seed `materias_primas` |
| Recebimento na rodada seguinte (D+1) | §7.2 | `CONFORME` | `CompraMateriaPrima.rodada_pedido` |
| Frete de MP a R$ 1,50/km | §7.2 | `CONFORME` | `services/materias_primas.calcular_frete` |
| Armazenagem de MP a 2% do valor de compra | §7.4 | `CONFORME` | `fechar_rodadas` |
| Fornecedores por cidade | §7.1 | `CONFORME` | `views.MATERIA_PRIMA_FORNECEDORES` |
| Desconto logístico cruzado de R$ 0,50/km | §7.2.1 | `DIVERGENTE` | **duas implementações conflitantes**: `services/materias_primas.py` usa R$ 0,50/km (correto), `views.FATOR_DESCONTO_LOGISTICO_CRUZADO` usa 10% |
| Frete de produtos acabados | §9.2a (decidido D10) | `CONFORME` | mesmo modelo de caminhão da compra de MP |

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
| Fator de marketing: `Mc = 1 + 0,20 · ln(1+Ic) / ln(1+10000)` | §14.1.1 | `DIVERGENTE` | `views.calcular_fator_marketing` usa modelo linear por `ganho_por_base`; a fórmula estava em imagem, recuperada em 2026-09-18 (`ORION-C-06`) |
| Salário do operador R$ 1.800/mês | §14.2.4, §14.3 | `CONFORME` | `CUSTO_OPERADOR_POR_RODADA`: cada rodada fecha uma folha integral, sem pró-rata de calendário |
| Custo da máquina R$ 8.000 | §14.2.4 | `NAO_VERIFICADO` | — |
| Limite de expansão de +50% sobre as máquinas iniciais | §14.2.1 | `AUSENTE` | sem validação |

### 4.6 Eventos aleatórios

| Regra | Origem | Status | Onde |
|---|---|---|---|
| Sorteio automático por rodada | §8.2 | `CONFORME` | `views.sortear_evento` + comando agendado |
| Evento aplicado igualmente a todos os grupos | §8.2 | `CONFORME` | `EventoRodada` por rodada |
| Os 6 eventos nomeados do §8.4 | §8.4 | `CONFORME` | `seed_dados_base` |
| Probabilidades 15 / 20 / 20 / 15 / 15 / 15 | §8.4 | `CONFORME` | `seed_dados_base` + sorteio ponderado em `services/eventos.py` |
| Impactos específicos por evento (ex.: greve retém 30% das entregas) | §8.4 | `CONFORME` | `services/retencao.py` + `Evento.retencao_entregas_percent` |
| Frase indicativa por evento | §8.5 | `CONFORME` | `Evento.frase_indicativa`, exibida no boletim |
| Até 2 eventos simultâneos | RN-10 | `AUSENTE` | decidido B4: 1 por rodada. "Até 2" fica como Sprint 29 |

### 4.7 Fechamento, financeiro e ranking

| Regra | Origem | Status | Onde |
|---|---|---|---|
| Fechamento automático no prazo | §11.1 | `CONFORME` | comando `fechar_rodadas` agendado |
| Bloqueio de edição após o prazo | §11.1 | `CONFORME` | `permite_edicao` |
| Penalidade de 10% por não submeter | §11.2, RN-04 | `CONFORME` | `services/fechamento.py` (aplica sobre `grupo.capital`; a spec diz "caixa ao final da rodada anterior" — diferença menor, vale ratificar) |
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
| **Encerramento da rodada** | CEO | `AUSENTE` | template existe (`financeiro/encerramento.html`), sem view nem rota |
| **Relatórios comparativos** | todos | `AUSENTE` | templates existem (`dashboard/*.html`), sem view nem rota |
| **Classificação final** | todos | `AUSENTE` | template existe (`classificacao.html`), sem view nem rota |
| **Gerenciamento do jogo** (monitorar participação) | professor | `CONFORME` | `/gerenciamento/` |
| **Painel de controle / Suporte** | professor | `AUSENTE` | — |

---

## 5. Backlog priorizado

IDs no formato `ORION-C-nn` (C de conformidade), para não colidir com os IDs
antigos do `docs/BACKLOG.md`.

### P0 — decisões que destravam o resto

- `ORION-C-01` `CONCLUIDO` (2026-09-18) — B1 a B5 decididos pela política "a
  documentação decide"; ver seção 3. **B5 tem confiança baixa** e vale ratificar
  com o Dr. Pio.
- `ORION-C-26` `BLOQUEADO` — B6 e B7 (frete de produtos acabados e unidade do
  frete de MP) seguem sem decisão. Nenhum trabalho de logística deve começar
  antes: o §7.2.1, como escrito, torna a primeira compra inviável.
- `ORION-C-02` `AUSENTE` — Unificar o desconto logístico cruzado. Hoje há duas
  implementações divergentes da mesma regra; a de `services/materias_primas.py`
  é a que segue a especificação. Remover a outra.

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
- `ORION-C-10` — Documentar ou corrigir a taxa de frete de produtos acabados
  (hoje R$ 0,10/km/unidade, sem origem documental).
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
  `capacidade_maquina = 100`; a capacidade efetiva permanece 400 minutos por
  máquina e produto, conforme §13.4 e decisão B3.
- `ORION-C-21` `CONCLUIDO` (2026-09-19) — Removido `services/vendas.py` e seu
  teste isolado: contrariavam a alocação competitiva entre grupos definida na
  §9.2(c) e já implementada em `fechar_rodadas.py`.
- `ORION-C-22` — Consertar a trilha principal de migrations, hoje inconsistente
  (`no such column: CONFIG.ranking_pesos`). Só `migrations_ci` sobe limpa.
- `ORION-C-23` `CONCLUIDO` (2026-09-18, verificado em 19/09) — Cobrir `export_resultados_pdf` e `export_resultados_excel`
  com teste (52 linhas sem execução; CSV e JSON já têm).
- `ORION-C-24` `CONCLUIDO` (2026-09-18, verificado em 19/09) — Cobrir `PainelGrupoView.post` (63 de 176 linhas sem execução). Seguem sem teste o bloqueio de produção por evento de estado e os multiplicadores percentuais de evento sobre custo.
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
  dos caminhos de erro de `PainelGrupoView.post` (capital, estoque e escopo).
  Seguem sem teste o bloqueio de produção por evento de estado e os
  multiplicadores percentuais de evento sobre custo.

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
