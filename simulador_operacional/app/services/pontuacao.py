"""Classificacao multicriterio dos grupos -- documento 12.

O 12.2 define cinco eixos (EO, DF, EE, SD, DS) combinados por pesos que
somam 1. Ate aqui o fechamento pontuava por quatro metricas proprias
(lucro/market share/atendimento/eficiencia) que nao existem no documento, e
Sustentabilidade simplesmente nao era calculada.

Cada eixo devolve um percentual de 0 a 100. O EE e o IE sao giro de
estoque expresso como percentual do fluxo -- ver `eficiencia_estoques`, que
explica por que a razao crua do 12.3.3 foi reescrita sem mudar a ordem que
ela produz.

A tabela de exemplo do 12.6 traz VALORES ILUSTRATIVOS, nao resultados
reais -- confirmado pelo Product Owner em 2026-09-24. Ela nao reproduz a
formula do 12.2 com os pesos do 12.4 (G1 daria 77,90 e a tabela declara
75,35; G2, 74,90 contra 72,55; G3, 74,75 contra 73,60) e nenhuma combinacao
de pesos multiplos de 0,05 explica as tres linhas. Nao serve de gabarito:
vale a formula.
"""

from decimal import Decimal

from django.db.models import Max, Sum

from app.parametros import (
    DISTANCIA_REGIONAL_KM,
    PESOS_DF,
    PESOS_DS,
    PESOS_EIXOS,
    PESOS_EO,
)

CEM = Decimal("100")


def _dec(valor):
    return valor if isinstance(valor, Decimal) else Decimal(str(valor or 0))


def _razao(numerador, denominador):
    """Razao segura. Denominador zerado significa "nao houve atividade"."""
    denominador = _dec(denominador)
    if denominador <= 0:
        return Decimal("0")
    return _dec(numerador) / denominador


def eficiencia_operacional(
    *, minutos_produzidos, minutos_de_capacidade, vendidos, disponiveis, perdas, base_perdas
):
    """12.3.1 -- producao, comercializacao e perdas, pesos F1/F2/F3.

    O primeiro termo e "Producao Liquida / Capacidade Utilizada". Ate
    2026-09-24 o codigo usava produzido/planejado, que e outra coisa:
    aderencia ao plano. Um grupo que planejava 100 e produzia 100 tirava
    nota cheia ocupando 3% da fabrica.

    A razao e minuto sobre minuto porque essa e a unidade do proprio
    documento: a tabela do 13.4 chama de "Capacidade Total por Rodada" e
    mede em minutos (15 maquinas x 400 min = 6.000 min/rodada). Somar
    unidades entre A, B e C distorceria -- uma unidade de A custa 2 min e
    uma de C custa 5.

    "Capacidade Utilizada" e a capacidade que o grupo pode de fato operar:
    maquinas com os dois operadores que o 14.2.3 exige. Maquina comprada e
    nao guarnecida nao entra, como manda o proprio 14.2.3.
    """
    f1, f2, f3 = PESOS_EO
    aproveitamento = Decimal("1") - _razao(perdas, base_perdas)
    return CEM * (
        min(_razao(minutos_produzidos, minutos_de_capacidade), Decimal("1")) * f1
        + _razao(vendidos, disponiveis) * f2
        + aproveitamento * f3
    )


def eficiencia_estoques(*, custo_das_vendas, estoque_medio):
    """Giro de estoque como percentual do fluxo -- 12.3.3.

    EE = 100 x CV / (CV + Estoque Medio)

    Serve ao IE do 12.3.2 e ao EE do 12.3.3: a formula e a mesma, o que muda
    e o estoque no denominador (total ou operacional).

    E a razao do documento, reescrita. Chamando g = CV/EM, o giro que o
    12.3.3 define, esta expressao e 100 x g/(g+1) -- transformacao
    estritamente crescente, entao a ORDEM entre as equipes e identica a que
    a formula do documento produz. Muda so a escala, de [0, infinito) para
    [0, 100], que e a dos outros quatro eixos do 12.2.

    Por que mudou (decisao do Rafael em 2026-09-24, medida antes de decidir):
    a razao pura explode quando o estoque medio encolhe, e nenhum dos 15
    documentos define teto ou o caso do denominador zero. Numa turma medida
    de oito rodadas com seis politicas de estoque, 26 das 42 observacoes
    ficaram fora de 0-100, com EE chegando a 19.800, e a equipe que vendeu
    TODO o estoque -- a politica que o 12.3.3 diz incentivar, "enxuta e
    agil" -- terminou em QUARTO lugar, porque estoque medio zero caia no
    _razao(x, 0) = 0. Com esta forma, a mesma turma ficou 42/42 dentro da
    escala e a classificacao passou a seguir exatamente a qualidade da
    decisao de estoque.

    Estoque medio zero com venda passa a valer 100 por construcao, sem
    regra a parte. Sem venda continua valendo 0: nao houve operacao a medir.
    """
    cv = _dec(custo_das_vendas)
    if cv <= 0:
        return Decimal("0")
    return CEM * cv / (cv + _dec(estoque_medio))


def desempenho_financeiro(*, lucro, receita, ativos_medios, custo_das_vendas, estoque_medio):
    """12.3.2 -- lucratividade, ROA e giro financeiro, pesos W1/W2/W3."""
    w1, w2, w3 = PESOS_DF
    il = CEM * _razao(lucro, receita)
    ir = CEM * _razao(lucro, ativos_medios)
    ie = eficiencia_estoques(custo_das_vendas=custo_das_vendas, estoque_medio=estoque_medio)
    return il * w1 + ir * w2 + ie * w3


def satisfacao_demanda(*, vendidos, capacidade_de_venda):
    """12.3.4 -- "grau de atendimento ao mercado".

    SD = (unidades vendidas / capacidade de venda da planta) x 100, com teto
    em 100. A capacidade vem do 13.5: o que as linhas do grupo conseguem
    colocar no mercado numa rodada, ja descontada a maquina sem os dois
    operadores do 14.2.3.

    O 12.3.4 nao traz formula para o SD -- o documento poe titulo e glosa do
    SD sobre a formula do DS (B8 no guia). O Product Owner definiu em
    2026-09-23 "vendidas / soma das demandas maximas de TODAS as pracas", e
    disso ficam duas escolhas dele, intactas:

    - VENDIDAS, nao entregues: despejar 5.000 unidades numa praca de demanda
      1.000 entrega cinco vezes mais e satisfaz o mesmo. Entregue/disponivel
      ja e o segundo termo do EO.
    - Denominador calculado, nunca digitado.

    O que mudou em 2026-09-24, e por que: o mercado do 9.1 soma 198.000
    unidades por rodada e a planta do 13.4 produz 5.300 -- o denominador era
    37 vezes maior que o numerador maximo. O eixo ficava preso em [0; 2,68],
    e com peso 0,20 contribuia no maximo 0,54 de 100. Pior, sendo o
    denominador uma constante, o SD ordenava por unidades vendidas e nada
    mais: tres estrategias opostas que venderam 3.000 empatavam em 1,52.

    Medido antes de decidir. Trocar para a demanda das PRACAS-ALVO -- a
    leitura que o 12.3.4 sugere -- inverteu o incentivo: quem vendeu 2.500
    em duas pracas pequenas tirava 83,33 e quem vendeu 3.000 espalhado por
    oito pracas tirava 4,76. E o risco que o Product Owner nomeou ao
    escolher o denominador global, e a medicao confirmou.

    A capacidade de venda e uma transformacao LINEAR CRESCENTE de vendidas,
    entao preserva exatamente a ordem que a formula ratificada produz --
    mesmo criterio do B11 (escala do giro de estoque). Muda so a escala,
    para a faixa 0-100 dos outros eixos.

    Correlacao declarada: o EO ja olha producao/capacidade e vendidos/
    enviados. O SD passa a olhar vendidos/capacidade, que os aproxima. Nao
    sao a mesma medida -- o EO mede disciplina de despacho, o SD mede quanto
    do potencial da fabrica virou venda --, mas andam juntos, e o 12 ja tem
    sobreposicoes assim (IE dentro do DF e EE, perdas no EO3 e no DS1).

    Teto em 100: quem vende estoque acumulado de rodadas anteriores pode
    passar da capacidade da rodada.
    """
    return CEM * min(_razao(vendidos, capacidade_de_venda), Decimal("1"))


def capacidade_de_venda(grupo):
    """Unidades que as linhas do grupo colocam no mercado numa rodada (13.5)."""
    return sum(
        linha.capacidade_unidades_rodada
        for linha in grupo.capacidades_produto.select_related("produto")
    )


def satisfacao_por_praca(*, grupo, rodada):
    """SD Local de cada praca atendida, para o mapa de calor do painel.

    A nota usa a SD Global; isto aqui e diagnostico -- mostra ao grupo onde
    ele deixou demanda na mesa.
    """
    from app.models import DemandaCidadeProduto, Distribuicao

    envios = Distribuicao.objects.filter(grupo=grupo, rodada=rodada).select_related(
        "cidade", "produto"
    )
    vendidas = {}
    cidades = {}
    for envio in envios:
        cidades[envio.cidade_id] = envio.cidade
        vendidas[envio.cidade_id] = vendidas.get(envio.cidade_id, 0) + envio.quantidade_vendida

    demandas = {}
    for linha in DemandaCidadeProduto.objects.filter(
        produto__ativo=True, cidade_id__in=cidades
    ):
        demandas[linha.cidade_id] = demandas.get(linha.cidade_id, 0) + linha.demanda_maxima

    linhas = []
    for cidade_id, cidade in cidades.items():
        demanda = demandas.get(cidade_id) or cidade.demanda
        vendida = vendidas.get(cidade_id, 0)
        linhas.append(
            {
                "cidade": cidade,
                "vendidas": vendida,
                "demanda": demanda,
                "percentual": CEM * min(_razao(vendida, demanda), Decimal("1")),
            }
        )
    return sorted(linhas, key=lambda linha: -linha["percentual"])


def sustentabilidade(
    *,
    perdas,
    base_perdas,
    distancia_media_compras,
    distancia_maxima,
    enviados_regionais,
    enviados_total,
):
    """12.3.4 -- perdas evitadas, proximidade da compra e entrega regional."""
    s1, s2, s3 = PESOS_DS
    ds1 = Decimal("1") - _razao(perdas, base_perdas)
    ds2 = Decimal("1") - min(_razao(distancia_media_compras, distancia_maxima), Decimal("1"))
    ds3 = _razao(enviados_regionais, enviados_total)
    return CEM * (ds1 * s1 + ds2 * s2 + ds3 * s3)


def pontuacao_total(eixos, pesos=None):
    """12.2 -- combinacao ponderada dos cinco eixos."""
    pesos = pesos or PESOS_EIXOS
    return sum((_dec(eixos.get(sigla)) * peso for sigla, peso in pesos.items()), Decimal("0"))


def ordenar_classificacao(linhas):
    """12.5 -- pontuacao, depois EO, SD, DS, receita bruta e nome.

    `linhas` e uma sequencia de dicts com as chaves `pontuacao`, `EO`, `SD`,
    `DS`, `receita` e `nome`.

    O RN-12 lista outro desempate para a mesma pontuacao final -- lucro
    acumulado, market share medio, saldo de caixa, penalidades. O Product
    Owner ratificou o 12.5 em 2026-09-24: e o documento marcado "Pronto", o
    12 inteiro e dedicado a classificacao, e os quatro primeiros criterios
    sao os proprios eixos da nota em ordem de peso.

    Adotar o RN-12 criaria contradicao interna: ele premiaria o saldo de
    caixa que o IR do 12.3.2 trata como ativo improdutivo, na mesma tela.
    A implementacao concorrente que existia em services/classificacao.py,
    orfa desde que o 12 entrou, foi removida na mesma data.
    """
    return sorted(
        linhas,
        key=lambda linha: (
            -_dec(linha.get("pontuacao")),
            -_dec(linha.get("EO")),
            -_dec(linha.get("SD")),
            -_dec(linha.get("DS")),
            -_dec(linha.get("receita")),
            (linha.get("nome") or "").casefold(),
        ),
    )


# --- Coleta dos insumos ----------------------------------------------------


def valor_dos_estoques(grupo):
    """Estoque a preco de custo, separado em materia-prima e acabado.

    O 12 pede dois denominadores diferentes, nao um: o IE do 12.3.2 e a
    "Eficiencia de Estoques (financeira)" e olha o ativo de estoque inteiro;
    o EE do 12.3.3 mede "eficiencia logistica operacional" sobre o "Estoque
    Medio Operacional" -- o produto acabado, que e o que gira na operacao
    comercial. O 7.4 e o 13.8 ja tratam os dois estoques como coisas
    distintas, com custo de armazenagem proprio para cada um.

    Devolve (total, operacional).
    """
    from app.models import EstoqueMateriaPrima, EstoqueProduto

    materia_prima = sum(
        (
            _dec(lote.quantidade_kg) * lote.materia_prima.preco_unitario
            for lote in EstoqueMateriaPrima.objects.filter(grupo=grupo).select_related(
                "materia_prima"
            )
        ),
        Decimal("0"),
    )
    operacional = sum(
        (
            Decimal(lote.quantidade) * lote.produto.custo_unitario_estimado
            for lote in EstoqueProduto.objects.filter(grupo=grupo).select_related("produto")
        ),
        Decimal("0"),
    )
    return materia_prima + operacional, operacional


def coletar_insumos(
    *,
    grupo,
    rodada,
    perdas,
    lucro,
    receita,
    saldo_caixa,
    valor_estoques_anterior=None,
    valor_operacional_anterior=None,
):
    """Numeros brutos da rodada, prontos para as formulas do 12.

    `perdas` ja vem do fechamento em reais (pereciveis + quebra), entao as
    razoes de perda ficam todas em valor -- perda sobre estoque existente,
    nao unidade sobre unidade.
    """
    from app.models import Cidade, CompraMateriaPrima, Distribuicao, Producao

    # 12.3.1: producao e capacidade em minutos, a unidade da tabela do 13.4.
    minutos_produzidos = sum(
        (
            Decimal(producao.quantidade_produzida) * producao.produto.tempo_producao_min
            for producao in Producao.objects.filter(
                grupo=grupo, rodada=rodada
            ).select_related("produto")
            if producao.produto
        ),
        Decimal("0"),
    )
    minutos_de_capacidade = sum(
        (
            Decimal(min(linha.maquinas, linha.operadores // 2) * linha.minutos_por_maquina)
            for linha in grupo.capacidades_produto.all()
        ),
        Decimal("0"),
    )

    envios = list(
        Distribuicao.objects.filter(grupo=grupo, rodada=rodada).select_related("produto", "cidade")
    )
    vendidos = sum(envio.quantidade_vendida for envio in envios)
    ofertados = sum(envio.quantidade for envio in envios)
    regionais = sum(
        envio.quantidade for envio in envios if envio.cidade.distancia_km <= DISTANCIA_REGIONAL_KM
    )
    custo_das_vendas = sum(
        (
            Decimal(envio.quantidade_vendida) * envio.produto.custo_unitario_estimado
            for envio in envios
            if envio.produto
        ),
        Decimal("0"),
    )

    compras = list(
        CompraMateriaPrima.objects.filter(grupo=grupo, rodada_pedido=rodada).select_related(
            "cidade_fornecedora"
        )
    )
    kg_comprado = sum((_dec(compra.quantidade_kg) for compra in compras), Decimal("0"))
    km_ponderado = sum(
        (_dec(compra.quantidade_kg) * compra.cidade_fornecedora.distancia_km for compra in compras),
        Decimal("0"),
    )

    valor_estoques, valor_operacional = valor_dos_estoques(grupo)
    if valor_estoques_anterior is None:
        valor_estoques_anterior = valor_estoques
    if valor_operacional_anterior is None:
        valor_operacional_anterior = valor_operacional
    # 12.3.3: "Estoque Medio = (Estoque Inicial + Estoque Final) / 2"
    estoque_medio = (_dec(valor_estoques_anterior) + valor_estoques) / Decimal("2")
    estoque_medio_operacional = (
        _dec(valor_operacional_anterior) + valor_operacional
    ) / Decimal("2")

    return {
        "minutos_produzidos": minutos_produzidos,
        "minutos_de_capacidade": minutos_de_capacidade,
        "vendidos": vendidos,
        "disponiveis": ofertados,
        "perdas": _dec(perdas),
        # o estoque perdido ja saiu do saldo: a base e o que existia antes
        "base_perdas": valor_estoques + _dec(perdas),
        "lucro": _dec(lucro),
        "receita": _dec(receita),
        "ativos_medios": _dec(saldo_caixa) + estoque_medio,
        "custo_das_vendas": custo_das_vendas,
        "estoque_medio": estoque_medio,
        "estoque_medio_operacional": estoque_medio_operacional,
        "valor_estoques": valor_estoques,
        "valor_estoques_operacional": valor_operacional,
        "capacidade_de_venda": capacidade_de_venda(grupo),
        "distancia_media_compras": _razao(km_ponderado, kg_comprado),
        "distancia_maxima": Cidade.objects.aggregate(m=Max("distancia_km"))["m"] or 0,
        "enviados_regionais": regionais,
        "enviados_total": ofertados,
    }


def calcular_eixos(insumos):
    """Os cinco eixos a partir do dicionario de `coletar_insumos`."""
    eixos = {
        "EO": eficiencia_operacional(
            minutos_produzidos=insumos["minutos_produzidos"],
            minutos_de_capacidade=insumos["minutos_de_capacidade"],
            vendidos=insumos["vendidos"],
            disponiveis=insumos["disponiveis"],
            perdas=insumos["perdas"],
            base_perdas=insumos["base_perdas"],
        ),
        "DF": desempenho_financeiro(
            lucro=insumos["lucro"],
            receita=insumos["receita"],
            ativos_medios=insumos["ativos_medios"],
            custo_das_vendas=insumos["custo_das_vendas"],
            estoque_medio=insumos["estoque_medio"],
        ),
        # 12.3.3: EE sobre o Estoque Medio OPERACIONAL. O IE de mesma
        # formula vive dentro do DF e usa o estoque total (12.3.2).
        "EE": eficiencia_estoques(
            custo_das_vendas=insumos["custo_das_vendas"],
            estoque_medio=insumos["estoque_medio_operacional"],
        ),
        "SD": satisfacao_demanda(
            vendidos=insumos["vendidos"],
            capacidade_de_venda=insumos["capacidade_de_venda"],
        ),
        "DS": sustentabilidade(
            perdas=insumos["perdas"],
            base_perdas=insumos["base_perdas"],
            distancia_media_compras=insumos["distancia_media_compras"],
            distancia_maxima=insumos["distancia_maxima"],
            enviados_regionais=insumos["enviados_regionais"],
            enviados_total=insumos["enviados_total"],
        ),
    }
    eixos["pontuacao"] = pontuacao_total(eixos)
    return eixos
