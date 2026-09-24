from decimal import Decimal

from ..models import Cidade, Distribuicao, MarketShareCidadeProduto


def distribuir_demanda(rodada: int) -> None:
    """Distribui a demanda das cidades entre os grupos na rodada."""
    for cidade in Cidade.objects.all():
        envios = list(
            Distribuicao.objects.filter(cidade=cidade, rodada=rodada).select_related("grupo", "produto")
        )
        if not envios:
            continue

        envios.sort(key=lambda e: Decimal(e.preco_unitario))

        demanda_restante = cidade.limite_demanda if cidade.limite_demanda > 0 else cidade.demanda
        for envio in envios:
            if demanda_restante <= 0:
                vendas = 0
            else:
                vendas = min(envio.quantidade, demanda_restante)

            envio.quantidade_vendida = vendas
            envio.quantidade_sobra = max(envio.quantidade - vendas, 0)
            envio.receita_realizada = (Decimal(vendas) * envio.preco_unitario).quantize(Decimal("0.01"))
            envio.processada = True
            envio.save(
                update_fields=[
                    "quantidade_vendida",
                    "quantidade_sobra",
                    "receita_realizada",
                    "processada",
                ]
            )

            if envio.produto_id:
                MarketShareCidadeProduto.objects.update_or_create(
                    grupo=envio.grupo,
                    cidade=cidade,
                    produto=envio.produto,
                    rodada=rodada,
                    defaults={"quantidade_vendida": vendas, "market_share_percent": Decimal("0")},
                )

            demanda_restante -= vendas


def executar_expedicao(*, grupo, rodada, evento=None):
    """Baixa o acabado e cobra o frete -- no fechamento, nao na submissao.

    O 11.3.b lista "Producao, vendas, compras, distribuicao" entre as acoes
    executadas no fechamento, nessa ordem: a expedicao acontece DEPOIS da
    producao, senao a equipe nao conseguiria enviar o que produziu na mesma
    rodada. Que e a mesma rodada, o 6.2 prova ao falar do produto B --
    "perde validade apos 1 rodada; unidades nao comercializadas ate o
    encerramento da rodada sao descartadas". Se o B so pudesse ser enviado
    na rodada seguinte, seria invendavel por construcao.

    Envio sem estoque suficiente sai parcial, pelo mesmo principio do 13.11,
    e o 13.10 so admite "a venda de produtos validos e disponiveis".

    Devolve (custo_do_frete, ajustes) -- o RN-05 pede alerta ao CEO.
    """
    from decimal import Decimal

    from .estoque import consumir_estoque_produto, estoque_disponivel_produto
    from .logistica import calcular_frete, peso_do_envio

    custo_total = Decimal("0")
    ajustes = []

    envios = Distribuicao.objects.filter(
        grupo=grupo, rodada=rodada, expedida=False, produto__isnull=False
    ).select_related("produto", "cidade")

    for envio in envios:
        pedido = int(envio.quantidade)
        disponivel = estoque_disponivel_produto(grupo, envio.produto)
        enviado = min(pedido, disponivel)

        if enviado < pedido:
            ajustes.append(
                {"produto": envio.produto, "cidade": envio.cidade,
                 "pedido": pedido, "enviado": enviado}
            )

        if enviado > 0:
            consumir_estoque_produto(
                grupo=grupo, produto=envio.produto, quantidade=enviado
            )
            # 9.2a: frete proporcional a distancia e ao volume.
            frete = calcular_frete(
                distancia_km=envio.cidade.distancia_km,
                peso_kg=peso_do_envio(envio.produto, enviado),
            )
            custo = frete["custo"]
            if (
                evento
                and evento.modo_aplicacao == "percentual"
                and evento.tipo == "custo_transporte"
            ):
                custo *= Decimal(1 + evento.impacto_percentual / 100)
        else:
            custo = Decimal("0")

        envio.quantidade = enviado
        envio.custo_transporte = custo
        envio.expedida = True
        envio.save(update_fields=["quantidade", "custo_transporte", "expedida"])
        custo_total += custo

    return custo_total, ajustes
