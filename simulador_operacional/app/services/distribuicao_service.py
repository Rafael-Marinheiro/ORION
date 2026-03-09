from decimal import Decimal

from ..models import Cidade, Distribuicao, VendaCidade


def distribuir_demanda(rodada: int) -> None:
    """Distribui a demanda das cidades entre os grupos na rodada.

    A prioridade de venda é determinada pela combinação de preço e fator
    de marketing. Grupos com menor razão ``preço / fator_marketing`` têm
    preferência sobre a demanda disponível. A quantidade vendida é
    limitada pela quantidade enviada por cada grupo.
    """
    for cidade in Cidade.objects.all():
        envios = list(
            Distribuicao.objects.filter(cidade=cidade, rodada=rodada).select_related("grupo")
        )
        if not envios:
            continue

        # Ordena por score: menor preço e maior marketing primeiro
        envios.sort(key=lambda e: (Decimal(e.preco_unitario) / (e.fator_marketing or Decimal("1"))))

        demanda_restante = cidade.demanda
        for envio in envios:
            if demanda_restante <= 0:
                vendas = 0
            else:
                vendas = min(envio.quantidade, demanda_restante)
            envio.vendas_realizadas = vendas
            envio.save(update_fields=["vendas_realizadas"])
            VendaCidade.objects.update_or_create(
                grupo=envio.grupo,
                cidade=cidade,
                rodada=rodada,
                defaults={"quantidade_vendida": vendas},
            )
            demanda_restante -= vendas
