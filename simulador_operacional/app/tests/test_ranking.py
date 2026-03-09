import pytest
from decimal import Decimal

from app.models import Grupo, Cidade, Distribuicao, ResultadoFinanceiro
from app.services.classificacao import calcular_ranking


@pytest.mark.django_db
def test_ranking_prioritizes_operational_efficiency():
    cidade = Cidade.objects.create(nome="X", distancia_km=10, demanda=100)
    g1 = Grupo.objects.create(nome="G1", capital=1000)
    g2 = Grupo.objects.create(nome="G2", capital=1000)

    # Ambos vendem 50, mas g1 envia menos, sendo mais eficiente
    Distribuicao.objects.create(
        grupo=g1,
        cidade=cidade,
        rodada=1,
        quantidade=60,
        preco_unitario=10,
        custo_transporte=0,
        vendas_realizadas=50,
    )
    Distribuicao.objects.create(
        grupo=g2,
        cidade=cidade,
        rodada=1,
        quantidade=100,
        preco_unitario=10,
        custo_transporte=0,
        vendas_realizadas=50,
    )

    ResultadoFinanceiro.objects.create(
        grupo=g1,
        rodada=1,
        lucro=Decimal("200"),
        saldo_caixa=Decimal("1000"),
        penalidades=Decimal("0"),
    )
    ResultadoFinanceiro.objects.create(
        grupo=g2,
        rodada=1,
        lucro=Decimal("200"),
        saldo_caixa=Decimal("1000"),
        penalidades=Decimal("0"),
    )

    ranking = calcular_ranking()
    assert [g.nome for g in ranking] == ["G1", "G2"]


@pytest.mark.django_db
def test_ranking_resolves_tie_with_cash_balance():
    cidade = Cidade.objects.create(nome="X", distancia_km=10, demanda=100)
    g1 = Grupo.objects.create(nome="G1", capital=1000)
    g2 = Grupo.objects.create(nome="G2", capital=1000)

    for rodada in [1, 2]:
        Distribuicao.objects.create(
            grupo=g1,
            cidade=cidade,
            rodada=rodada,
            quantidade=50,
            preco_unitario=10,
            custo_transporte=0,
            vendas_realizadas=50,
        )
        Distribuicao.objects.create(
            grupo=g2,
            cidade=cidade,
            rodada=rodada,
            quantidade=50,
            preco_unitario=10,
            custo_transporte=0,
            vendas_realizadas=50,
        )

    ResultadoFinanceiro.objects.create(
        grupo=g1,
        rodada=2,
        lucro=Decimal("200"),
        saldo_caixa=Decimal("1000"),
        penalidades=Decimal("0"),
    )
    ResultadoFinanceiro.objects.create(
        grupo=g2,
        rodada=2,
        lucro=Decimal("200"),
        saldo_caixa=Decimal("800"),
        penalidades=Decimal("0"),
    )

    ranking = calcular_ranking()
    assert [g.nome for g in ranking] == ["G1", "G2"]


@pytest.mark.django_db
def test_ranking_resolves_tie_with_penalties():
    cidade = Cidade.objects.create(nome="X", distancia_km=10, demanda=100)
    g1 = Grupo.objects.create(nome="G1", capital=1000)
    g2 = Grupo.objects.create(nome="G2", capital=1000)

    for rodada in [1, 2]:
        Distribuicao.objects.create(
            grupo=g1,
            cidade=cidade,
            rodada=rodada,
            quantidade=50,
            preco_unitario=10,
            custo_transporte=0,
            vendas_realizadas=50,
        )
        Distribuicao.objects.create(
            grupo=g2,
            cidade=cidade,
            rodada=rodada,
            quantidade=50,
            preco_unitario=10,
            custo_transporte=0,
            vendas_realizadas=50,
        )

    ResultadoFinanceiro.objects.create(
        grupo=g1,
        rodada=2,
        lucro=Decimal("200"),
        saldo_caixa=Decimal("1000"),
        penalidades=Decimal("10"),
    )
    ResultadoFinanceiro.objects.create(
        grupo=g2,
        rodada=2,
        lucro=Decimal("200"),
        saldo_caixa=Decimal("1000"),
        penalidades=Decimal("20"),
    )

    ranking = calcular_ranking()
    assert [g.nome for g in ranking] == ["G1", "G2"]

