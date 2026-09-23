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
# MP: §7.2 define R$ 1,50 por km e por kg adquirido. Produto acabado: §9.2a
# exige proporcionalidade a distancia e volume, sem taxa; a calibracao do
# ORION usa referencia de carga geral da ANTT, arredondada para a aula.
CAPACIDADE_CAMINHAO_KG = 12000
CUSTO_MP_POR_KM_KG = Decimal("1.50")
CUSTO_VIAGEM_PRODUTO_POR_KM = Decimal("5.00")
CUSTO_CARGA_DESCARGA_PRODUTO = Decimal("500.00")

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

# --- Classificacao multicriterio (12) --------------------------------------
#
# Pesos dos cinco eixos, tabela 12.4. Somam 1.
PESOS_EIXOS = {
    "EO": Decimal("0.30"),
    "DF": Decimal("0.25"),
    "EE": Decimal("0.15"),
    "SD": Decimal("0.20"),
    "DS": Decimal("0.10"),
}

# Pesos internos: 12.3.1 (F), 12.3.2 (W) e 12.3.4 (S).
PESOS_EO = (Decimal("0.4"), Decimal("0.4"), Decimal("0.2"))
PESOS_DF = (Decimal("0.4"), Decimal("0.3"), Decimal("0.3"))
PESOS_DS = (Decimal("0.5"), Decimal("0.3"), Decimal("0.2"))

# SD nao tem pesos internos: o 12.3.4 traz titulo e glosa do SD sobre a
# formula do DS, e a formula do SD nao existe em nenhum dos 15 documentos.
# O Product Owner definiu em 2026-09-23:
#   SD = (unidades vendidas / soma das demandas maximas) x 100
# Denominador sobre TODAS as pracas e calculado em tempo de execucao --
# ver `satisfacao_demanda` e `demanda_total_do_mercado`.

# O DS3 do 12.3.4 premia entregas ate 1.000 km. No mapa regional a praca mais
# distante esta a 470 km, entao o limiar do documento daria 100% para todo
# mundo -- indicador inerte. Recalibrado para a escala do mapa que usamos.
DISTANCIA_REGIONAL_KM = 200

# --- Marketing (14.1) ------------------------------------------------------
#
# Mc = 1 + 0,20 x ln(1 + Ic) / ln(1 + 10000), com Ic limitado ao teto:
# "Investimentos superiores a R$ 10.000,00 nao geram aumento adicional".
#
# A tabela de exemplo do 14.1.3 nao reproduz essa formula (declara 1,038 para
# R$ 1.000 onde a formula da 1,150) e ainda salta de 1,051 para 1,200 entre
# R$ 5.000 e R$ 10.000 -- degrau que nenhuma curva logaritmica produz. Vale a
# formula, que e continua e bate nos dois extremos declarados (1,000 e 1,200).
INVESTIMENTO_MARKETING_TETO = Decimal("10000")
GANHO_MAXIMO_MARKETING = Decimal("0.20")

# --- Investimentos: limites (14.2.1 e RN-09) -------------------------------
#
# 14.2.1: "ate 50% sobre a quantidade inicial instalada", por restricao fisica
# do espaco industrial, "fixo durante toda a simulacao". O limite e sobre o
# parque do grupo, nao por linha de produto -- o que acaba e o galpao.
LIMITE_EXPANSAO_MAQUINAS = Decimal("0.5")

# RN-09 (5): "Saldo negativo (fluxo de caixa negativo) por duas rodadas
# consecutivas implica na restricao de investimento."
RODADAS_CAIXA_NEGATIVO_PARA_RESTRICAO = 2
