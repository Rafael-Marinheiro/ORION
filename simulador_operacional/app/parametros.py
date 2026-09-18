"""Parametros economicos da simulacao, rastreaveis a especificacao.

Cada constante aqui aponta para o trecho de `_documentacao/TXT/` que a define.
Quem mudar um valor deve mudar a referencia junto -- ou registrar a divergencia
em `docs/GUIA_IMPLEMENTACAO.md`.

Estavam duplicadas em `views.py` e em `management/commands/fechar_rodadas.py`,
com risco de divergirem em silencio.
"""

from decimal import Decimal

# 14.2.4 e 14.3: "Salario por funcionario: R$ 1.800,00/mes".
SALARIO_OPERADOR_MENSAL = Decimal("1800")

# A rodada e o periodo de competencia da folha, e nao um numero de semanas.
#
# O RN-06 diz que a rodada "representa uma semana", mas quem define a data de
# encerramento e o professor, livremente: uma rodada pode durar uma aula, um
# dia ou uma semana de calendario. Converter o salario por tempo decorrido
# amarraria a economia do jogo ao relogio de parede, e o custo da mesma
# decisao mudaria conforme o professor mexesse no prazo. Entao cada rodada
# fecha uma folha, e o valor e o do documento, sem conversao.
CUSTO_OPERADOR_POR_RODADA = SALARIO_OPERADOR_MENSAL

# 11.2 e RN-04: "multado em 10% sobre o valor disponivel em caixa ao final da
# rodada anterior".
PERCENTUAL_PENALIDADE_SEM_SUBMISSAO = Decimal("0.10")

# 14.4.1: "rendimento fixo de 1,5% por rodada".
TAXA_APLICACAO_FINANCEIRA_RODADA = Decimal("0.015")

# 13.4: "Cada maquina opera 400 minutos por rodada". Decisao B3 do guia.
MINUTOS_POR_MAQUINA_RODADA = 400

# 14.3: "Cada maquina em operacao exige dois funcionarios".
OPERADORES_POR_MAQUINA = 2

# 9.1 nao da uma formula, da uma tabela. Dividindo demanda por populacao nas
# 10 cidades listadas, a razao fica em 0,207% em media (min 0,148%, max
# 0,241%). E esse o fator usado para derivar a demanda das pracas a partir
# da populacao, em vez de digitar numero por cidade.
FATOR_DEMANDA_POR_HABITANTE = 0.00207

# Piso de demanda por praca. Sem ele, cidade pequena arredonda para zero e
# vira um destino onde o grupo envia e nao vende nada -- mercado quebrado,
# nao mercado pequeno.
DEMANDA_MINIMA_POR_PRACA = 50

# --- Logistica -------------------------------------------------------------
#
# O 7.2 diz "R$ 1,50 por quilometro rodado, multiplicado pela quantidade
# adquirida (em kg)". Essa unidade nao fecha: no exemplo do proprio 7.2.1,
# 500 kg de MP3 valendo R$ 4.000 geram R$ 750.000 de frete, 188x a carga.
#
# A unidade passa a ser por VIAGEM de caminhao (decisao D10 do guia). Os
# numeros do documento sao mantidos; o que muda e o que eles multiplicam.
# O caminhao indivisivel e o que torna o modelo didatico: consolidar pedido
# fica barato por quilo, comprar em migalhas fica caro.
CAPACIDADE_CAMINHAO_KG = 12000
CUSTO_VIAGEM_POR_KM = Decimal("1.50")

# 7.2.1: desconto por remessa cruzada. Fisicamente e o frete de retorno --
# o caminhao que levou produto volta carregado em vez de voltar vazio.
DESCONTO_RETORNO_POR_KM = Decimal("0.50")

# --- Variedade de eventos --------------------------------------------------
#
# O 8.2 pede probabilidade constante, mas rodar o mesmo evento em sequencia
# empobrece a aula. A saida nao e bloquear o evento recente -- bloqueio
# achata os pesos: medido com 3 eventos de pesos 60/30/10, um cooldown duro
# de 2 rodadas os transforma em 33/33/33, destruindo a configuracao em
# silencio.
#
# Aqui o peso do evento recente e REDUZIDO, nunca zerado. Ele continua
# possivel, so fica improvavel. Com os 6 eventos do 8.4 isso da 1,2% de
# repeticao consecutiva e no maximo 1,3 p.p. de desvio das probabilidades
# documentadas -- melhor nos dois criterios que o cooldown duro, que dava
# 1,5 p.p. de desvio.
#
# Chave = ha quantas rodadas o evento saiu. Valor = multiplicador do peso.
PENALIDADE_EVENTO_RECENTE = {1: 0.05, 2: 0.30, 3: 0.65}
