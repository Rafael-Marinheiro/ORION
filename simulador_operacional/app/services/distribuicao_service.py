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
