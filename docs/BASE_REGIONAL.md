> **Documento histórico.** A base regional do Seridó (D9.1–D9.3) foi revertida
> em 24/09/2026 a pedido do dono do projeto: o simulador voltou a usar a
> fábrica em Natal e as dez praças do §9.1, com a distância e o teto de
> absorção tabelados pelo Dr. Pio. As fontes abaixo ficam registradas porque
> explicam de onde vieram os números que estiveram em uso até essa data.

# Base regional validada — 20/09/2026

Fonte de regra: original DOCX 9, §9.1–9.2, confrontado com D9.1–D9.3 do guia de implementação. A sede e as 12 praças regionais são decisões já aprovadas.

População: [IBGE — Censo 2022, população com malha territorial de 2023, publicação DOU de 31/08/2023](https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/Relacao_da_Populacao_dos_Municipios_para_publicacao_no_DOU_em_2023/POP_DOU_2023_Municipios_POP2022_Malha2023.pdf). Consulta: 20/09/2026. É uma base censitária congelada e homogênea, não uma estimativa de 2026. Os códigos evitam confusão com municípios homônimos.

Distâncias: percurso rodoviário entre cidades, em km inteiros, consulta em 20/09/2026. As páginas não informam data de cálculo; a data registrada é a da consulta. Não são distâncias em linha reta nem medições entre endereços de galpões. A distância de Currais Novos para si mesma é 0 por definição da sede.

| Praça (nome no seed) / IBGE | População anterior → validada | Página IBGE | km anterior → validado | Fonte de rota | Demanda anterior → atual |
|---|---:|---:|---:|---|---:|
| Currais Novos / 2403103 | 45,000 → 41,313 | 23 | 0 → 0 | Sede D9.1 (origem = destino) | 100 → 100 |
| Acari / 2400109 | 11,000 → 10,597 | 23 | 23 → 29 | [Rota Mapas](https://www.rotamapas.com.br/distancia-entre-currais-novos-e-acari) | 50 → 50 |
| Caico / 2402006 | 68,000 → 61,146 | 23 | 75 → 88 | [Rota Mapas](https://www.rotamapas.com.br/distancia-entre-currais-novos-e-caico) | 150 → 150 |
| Santa Cruz / 2411205 | 40,000 → 37,313 | 25 | 95 → 64 | [Rota Mapas](https://www.rotamapas.com.br/distancia-entre-santa-cruz-rn-e-currais-novos) | 100 → 100 |
| Patos / 2510808 | 108,000 → 103,165 | 29 | 135 → 143 | [Rota Mapas](https://www.rotamapas.com.br/distancia-entre-currais-novos-e-patos) | 200 → 200 |
| Assu / 2400208 | 58,000 → 56,496 | 23 | 140 → 139 | [Distância Cidades](https://br.distanciacidades.net/distancia-de-currais-novos-a-acu) | 100 → 100 |
| Natal / 2408102 | 751,000 → 751,300 | 24 | 172 → 181 | [Rota Mapas](https://www.rotamapas.com.br/distancia-entre-currais-novos-e-natal) | 1550 → 1550 |
| Campina Grande / 2504009 | 419,000 → 419,379 | 27 | 190 → 167 | [Rota Mapas](https://www.rotamapas.com.br/distancia-entre-currais-novos-e-campina-grande) | 850 → 850 |
| Mossoro / 2408003 | 265,000 → 264,577 | 24 | 190 → 198 | [Rota Mapas](https://www.rotamapas.com.br/distancia-entre-mossoro-e-currais-novos) | 550 → 550 |
| Joao Pessoa / 2507507 | 833,000 → 833,932 | 28 | 300 → 263 | [Rota Mapas](https://www.rotamapas.com.br/distancia-entre-currais-novos-e-joao-pessoa) | 1700 → 1750 |
| Recife / 2611606 | 1,488,000 → 1,488,920 | 33 | 420 → 342 | [Rota Mapas](https://www.rotamapas.com.br/distancia-entre-currais-novos-e-recife) | 3100 → 3100 |
| Fortaleza / 2304400 | 2,428,000 → 2,428,708 | 20 | 470 → 437 | [Rota Mapas](https://www.rotamapas.com.br/distancia-entre-currais-novos-e-fortaleza) | 5050 → 5050 |

## Critério e diferenças

Todas as populações anteriores eram aproximações. Apenas Currais Novos mantém a distância anterior. Assu é o município Açu no IBGE; os nomes sem acentos usados pelo código foram preservados para manter as referências aos fornecedores.

O Rota Mapas foi mantido como referência comum onde disponível; para Açu, 139 km de condução também concordam com 138,6 km do Rome2Rio arredondados. Há variação por trajeto: Caicó aparece com 85,5 km no Rome2Rio e 88 km no Rota Mapas. Usamos a rota explicitamente citada na tabela, sem apresentar o número como distância única e exata.

Fórmula preservada: `max(50, round(população × 0,00207 / 50) × 50)`, com arredondamento Python para o múltiplo de 50 mais próximo (empate para par). A demanda total continua repartida em A 50%, B 30% e C 20%, como no seed anterior. Não é uma nova calibração.

O seed atualiza as 12 praças pelo nome e suas 36 demandas de produto, sem duplicar registros. Em base vazia há exatamente 12 cidades. Catálogos personalizados ou cidades nacionais de uma base antiga não são apagados automaticamente: preparar uma base limpa para a primeira turma. Não reaplicar seed durante uma partida, pois altera o catálogo global e os eventos.
