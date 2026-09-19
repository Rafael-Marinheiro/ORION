"""Classificacao multicriterio dos grupos -- documento 12.

O 12.2 define cinco eixos (EO, DF, EE, SD, DS) combinados por pesos que
somam 1. Ate aqui o fechamento pontuava por quatro metricas proprias
(lucro/market share/atendimento/eficiencia) que nao existem no documento, e
Sustentabilidade simplesmente nao era calculada.

Cada eixo devolve um percentual. EE e o giro de estoque, entao passa de 100
com naturalidade -- o proprio exemplo do 12.6 mostra EE de 102 a 110. Nao ha
teto artificial.

Divergencia registrada: a tabela de exemplo do 12.6 nao reproduz a formula
do 12.2 com os pesos do 12.4 (G1 daria 77,9 e a tabela declara 75,35). Como
nos outros casos do projeto, vale a versao internamente consistente -- a
formula e os pesos, que sao a parte normativa.
"""

from decimal import Decimal

from django.db.models import Max, Sum

from app.parametros import (
    DISTANCIA_REGIONAL_KM,
    PESOS_DF,
    PESOS_DS,
    PESOS_EIXOS,
    PESOS_EO,
    PESOS_SD,
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


def eficiencia_operacional(*, produzido, planejado, vendidos, disponiveis, perdas, base_perdas):
    """12.3.1 -- producao, comercializacao e perdas, pesos F1/F2/F3."""
    f1, f2, f3 = PESOS_EO
    aproveitamento = Decimal("1") - _razao(perdas, base_perdas)
    return CEM * (
        _razao(produzido, planejado) * f1
        + _razao(vendidos, disponiveis) * f2
        + aproveitamento * f3
    )


def eficiencia_estoques(*, custo_das_vendas, estoque_medio):
    """12.3.3 -- giro: custo das vendas sobre estoque medio, em %."""
    return CEM * _razao(custo_das_vendas, estoque_medio)


def desempenho_financeiro(*, lucro, receita, ativos_medios, custo_das_vendas, estoque_medio):
    """12.3.2 -- lucratividade, ROA e giro financeiro, pesos W1/W2/W3."""
    w1, w2, w3 = PESOS_DF
    il = CEM * _razao(lucro, receita)
    ir = CEM * _razao(lucro, ativos_medios)
    ie = eficiencia_estoques(custo_das_vendas=custo_das_vendas, estoque_medio=estoque_medio)
    return il * w1 + ir * w2 + ie * w3


def satisfacao_demanda(*, vendidos, demanda_potencial, pracas_atendidas, pracas_ativas):
    """Profundidade x cobertura. Formula do projeto -- ver PESOS_SD."""
    s1, s2 = PESOS_SD
    profundidade = min(_razao(vendidos, demanda_potencial), Decimal("1"))
    cobertura = min(_razao(pracas_atendidas, pracas_ativas), Decimal("1"))
    return CEM * (profundidade * s1 + cobertura * s2)


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
    """Estoque de MP mais estoque de produto acabado, a preco de custo."""
    from app.models import EstoqueMateriaPrima, EstoqueProduto

    total = Decimal("0")
    for lote in EstoqueMateriaPrima.objects.filter(grupo=grupo).select_related("materia_prima"):
        total += _dec(lote.quantidade_kg) * lote.materia_prima.preco_unitario
    for lote in EstoqueProduto.objects.filter(grupo=grupo).select_related("produto"):
        total += Decimal(lote.quantidade) * lote.produto.custo_unitario_estimado
    return total


def coletar_insumos(
    *, grupo, rodada, perdas, lucro, receita, saldo_caixa, valor_estoques_anterior=None
):
    """Numeros brutos da rodada, prontos para as formulas do 12.

    `perdas` ja vem do fechamento em reais (pereciveis + quebra), entao as
    razoes de perda ficam todas em valor -- perda sobre estoque existente,
    nao unidade sobre unidade.
    """
    from app.models import Cidade, CompraMateriaPrima, Distribuicao, Producao

    producoes = Producao.objects.filter(grupo=grupo, rodada=rodada).aggregate(
        produzido=Sum("quantidade_produzida"),
        planejado=Sum("quantidade_planejada"),
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
    cidades_alvo = {envio.cidade_id: envio.cidade for envio in envios}
    pracas_atendidas = len({envio.cidade_id for envio in envios if envio.quantidade_vendida > 0})
    demanda_potencial = sum(cidade.demanda for cidade in cidades_alvo.values())

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

    valor_estoques = valor_dos_estoques(grupo)
    if valor_estoques_anterior is None:
        valor_estoques_anterior = valor_estoques
    estoque_medio = (_dec(valor_estoques_anterior) + valor_estoques) / Decimal("2")

    return {
        "produzido": producoes["produzido"] or 0,
        "planejado": producoes["planejado"] or 0,
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
        "valor_estoques": valor_estoques,
        "demanda_potencial": demanda_potencial,
        "pracas_atendidas": pracas_atendidas,
        "pracas_ativas": Cidade.objects.filter(demanda__gt=0).count(),
        "distancia_media_compras": _razao(km_ponderado, kg_comprado),
        "distancia_maxima": Cidade.objects.aggregate(m=Max("distancia_km"))["m"] or 0,
        "enviados_regionais": regionais,
        "enviados_total": ofertados,
    }


def calcular_eixos(insumos):
    """Os cinco eixos a partir do dicionario de `coletar_insumos`."""
    eixos = {
        "EO": eficiencia_operacional(
            produzido=insumos["produzido"],
            planejado=insumos["planejado"],
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
        "EE": eficiencia_estoques(
            custo_das_vendas=insumos["custo_das_vendas"],
            estoque_medio=insumos["estoque_medio"],
        ),
        "SD": satisfacao_demanda(
            vendidos=insumos["vendidos"],
            demanda_potencial=insumos["demanda_potencial"],
            pracas_atendidas=insumos["pracas_atendidas"],
            pracas_ativas=insumos["pracas_ativas"],
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
