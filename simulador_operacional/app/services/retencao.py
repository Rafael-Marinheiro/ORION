"""Retencao de entregas por evento -- 8.4.

Dois eventos do 8.4 retem entregas: a greve de caminhoneiros (30%) e as
enchentes (20%). O texto das duas linhas e identico no que importa:

    "X% das entregas de MP e produtos sao retidas para a proxima rodada.
     Produtos pereciveis sao perdidos."

O codigo tratava isso como **queda de demanda** na cidade, o que e outra
coisa inteiramente: a carga continuava chegando, o mercado e que comprava
menos, e na rodada seguinte nao voltava nada. A licao do evento -- carga
parada na estrada, e perecivel parado e perecivel perdido -- nao acontecia.

Aqui a entrega e de fato retida: a parcela retida sai da rodada corrente e
reaparece como envio da rodada seguinte, sem cobrar frete de novo (o
caminhao ja saiu). Se o produto for perecivel, nao reaparece: vira perda,
com o mesmo custo que a perecibilidade normal usa.
"""

from decimal import ROUND_HALF_UP, Decimal


def _parcela_retida(quantidade, percentual):
    if quantidade <= 0 or percentual <= 0:
        return 0
    retido = (Decimal(quantidade) * Decimal(percentual) / Decimal("100")).to_integral_value(
        rounding=ROUND_HALF_UP
    )
    return min(int(retido), int(quantidade))


def aplicar_retencao_de_entregas(envios, percentual, rodada_numero):
    """Retem parte de cada envio. Devolve as perdas de perecivel por grupo.

    Altera `envios` no lugar: cada objeto fica com a quantidade que de fato
    vai a mercado nesta rodada.
    """
    from app.models import Distribuicao

    perdas_por_grupo = {}
    if percentual <= 0:
        return perdas_por_grupo

    for envio in envios:
        retido = _parcela_retida(envio.quantidade, percentual)
        if retido <= 0:
            continue

        envio.quantidade -= retido
        envio.save(update_fields=["quantidade"])

        if envio.produto and envio.produto.perecivel:
            perda = Decimal(retido) * envio.produto.custo_unitario_estimado
            perdas_por_grupo[envio.grupo_id] = perdas_por_grupo.get(
                envio.grupo_id, Decimal("0")
            ) + perda
            continue

        # o frete ja foi pago quando o envio saiu: a carga esta na estrada,
        # nao no deposito. Cobrar de novo puniria duas vezes o mesmo evento.
        # Pelo mesmo motivo nasce `expedida=True`: a baixa do estoque de
        # acabados aconteceu na expedicao desta rodada, e expedir de novo na
        # rodada seguinte consumiria o mesmo produto duas vezes.
        Distribuicao.objects.create(
            grupo_id=envio.grupo_id,
            produto_id=envio.produto_id,
            cidade_id=envio.cidade_id,
            rodada=rodada_numero + 1,
            quantidade=retido,
            preco_unitario=envio.preco_unitario,
            custo_transporte=Decimal("0"),
            expedida=True,
        )

    return perdas_por_grupo


def aplicar_retencao_de_materia_prima(compra, percentual, rodada_numero):
    """Retem parte de uma compra de MP para a rodada seguinte.

    Devolve os kg que chegam agora. Materia-prima nao perece neste modelo,
    entao a parcela retida so atrasa -- e o atraso ja e punicao suficiente
    para quem planejou a producao contando com ela.
    """
    from app.models import CompraMateriaPrima

    if percentual <= 0:
        return compra.quantidade_kg

    retido = (
        Decimal(compra.quantidade_kg) * Decimal(percentual) / Decimal("100")
    ).quantize(Decimal("0.01"))
    if retido <= 0:
        return compra.quantidade_kg

    CompraMateriaPrima.objects.create(
        grupo_id=compra.grupo_id,
        materia_prima_id=compra.materia_prima_id,
        cidade_fornecedora_id=compra.cidade_fornecedora_id,
        rodada_pedido=compra.rodada_pedido,
        rodada_recebimento=rodada_numero + 1,
        quantidade_kg=retido,
        preco_unitario=compra.preco_unitario,
        # os custos ficam na compra original: a carga e a mesma, so chega
        # partida em duas. Duplicar o frete inventaria um custo que nao houve.
        custo_logistico=Decimal("0"),
        desconto_logistico=Decimal("0"),
        valor_total=Decimal("0"),
        recebida=False,
    )

    compra.quantidade_kg -= retido
    compra.save(update_fields=["quantidade_kg"])
    return compra.quantidade_kg
