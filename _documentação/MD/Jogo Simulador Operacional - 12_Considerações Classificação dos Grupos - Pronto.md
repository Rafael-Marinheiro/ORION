> Extraido de `_documentação/DOC/` preservando tabelas. As formulas e os
> diagramas do documento original sao **imagens coladas**, sem texto: foram
> lidos e transcritos nos blocos marcados abaixo. A fonte de verdade continua
> sendo o `.docx`; este arquivo existe para o conteudo ser pesquisavel e
> versionado.

12. Considerações Classificação dos Grupos

12.1 Objetivo

O mecanismo de classificação dos grupos no simulador ORION visa avaliar o desempenho gerencial dos participantes em múltiplas dimensões estratégicas e operacionais, de forma integrada e pedagógica. A classificação não se limita ao lucro ou à produção, mas considera critérios de eficiência, responsabilidade ambiental, logística e atendimento ao mercado.

12.2 Estrutura Multicritério

A pontuação final de cada grupo será calculada por meio de um modelo multicritério ponderado, que considera cinco eixos estratégicos:

Eficiência Operacional (EO)

Desempenho Financeiro (DF)

Eficiência de Estoques (EE)

Satisfação da Demanda (SD)

Desempenho em Sustentabilidade (DS)

Fórmula Geral:

```
Pontuação Total (%) = (EO × P₁) + (DF × P₂) + (EE × P₃) + (SD × P₄) + (DS × P₅)
```

Os pesos P₁ a P₅ devem somar 1 e podem ser ajustados por rodada, conforme o foco pedagógico desejado.

12.3 Componentes e Fórmulas

12.3.1 Eficiência Operacional (EO)

Avalia a gestão integrada da produção, comercialização e perdas operacionais.

```
EO = (Produção Líquida / Capacidade Utilizada) × F₁
   + (Produtos Vendidos / Produtos Disponíveis) × F₂
   + (1 − Perdas Totais / (MP + Produtos)) × F₃
``` ​

Pesos internos: F₁ = 0,4 | F₂ = 0,4 | F₃ = 0,2

12.3.2 Desempenho Financeiro (DF)

Índice composto que avalia a saúde econômica do grupo.

```
DF = (IL × W₁) + (IR × W₂) + (IE × W₃)
```

Subindicadores:

IL – Lucratividade:

```
IL = (Lucro Líquido / Receita Bruta) × 100
```

IR – Rentabilidade sobre Ativos (ROA):

```
IR = (Lucro Líquido / Ativos Totais Médios) × 100
```

IE – Eficiência de Estoques (financeira):

```
IE = (Custo das Vendas / Estoque Médio) × 100
```

Pesos internos sugeridos: W₁ = 0,4 | W₂ = 0,3 | W₃ = 0,3

12.3.3 Eficiência de Estoques (EE)

Mede a eficiência logística operacional no uso de estoques:

```
EE = (Custo das Vendas / Estoque Médio Operacional) × 100
```

Estoque Médio = (Estoque Inicial + Estoque Final) / 2

Este indicador incentiva uma política de estoques enxuta e ágil.

12.3.4 Satisfação da Demanda (SD)

Avalia o grau de atendimento ao mercado nas praças-alvo:

```
DS = (DS₁ × S₁) + (DS₂ × S₂) + (DS₃ × S₃)
```

Componentes sugeridos:

DS₁ – Redução de Perdas Totais (MP + Produtos):

```
DS₁ = 1 − (Perdas Totais / (MP + Produtos))
```

DS₂ – Proximidade Logística das Compras de MP:

```
DS₂ = 1 − (Distância Média das Compras / Distância Máxima Teórica)
```

DS₃ – Otimização das Entregas (foco regional):

```
DS₃ = (Produtos Enviados para praças ≤ 1.000 km) / Total Enviado
```

Pesos internos sugeridos: S₁ = 0,5 | S₂ = 0,3 | S₃ = 0,2

12.4 Pesos Sugeridos por Critério (Rodada Padrão)



| Critério | Sigla | Peso (P) |
|---|---|---|
| Eficiência Operacional | EO | 0,30 |
| Desempenho Financeiro | DF | 0,25 |
| Eficiência de Estoques | EE | 0,15 |
| Satisfação da Demanda | SD | 0,20 |
| Sustentabilidade | DS | 0,10 |



12.5 Critérios de Desempate

Em caso de empate na pontuação final, serão aplicados os seguintes critérios, nesta ordem:

Maior Eficiência Operacional

Maior Satisfação da Demanda

Maior Desempenho em Sustentabilidade

Maior Receita Bruta

Ordem alfabética do nome do grupo

12.6 Exemplo de Cálculo



| Grupo | EO (%) | DF (%) | EE (%) | SD (%) | DS (%) | Pontuação Final (%) |
|---|---|---|---|---|---|---|
| G1 | 84 | 40 | 110 | 85 | 92 | 75,35 |
| G2 | 81 | 43 | 105 | 78 | 85 | 72,55 |
| G3 | 86 | 39 | 102 | 82 | 75 | 73,60 |



12.7 Aplicações Pedagógicas

Estimula decisões multidimensionais, promovendo a visão sistêmica da gestão empresarial.

Aborda competências associadas aos ODS (Objetivos de Desenvolvimento Sustentável).

Permite a customização das rodadas conforme o tema da aula, alterando pesos dos critérios.

Reforça conceitos de trade-offs entre eficiência, lucratividade, atendimento ao mercado e responsabilidade ambiental.