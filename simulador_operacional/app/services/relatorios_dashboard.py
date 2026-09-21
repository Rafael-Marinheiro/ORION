"""Agrega os consolidados de rodada para o painel visual de relatorios.

A leitura util para o aluno nao e o valor absoluto de uma rodada, e sim como
ele se move de uma rodada para a outra e de onde vem o custo. Por isso este
modulo devolve series por rodada, a composicao dos custos e a variacao contra
a rodada anterior, em vez de um retrato unico do periodo.
"""

from decimal import Decimal

ZERO = Decimal("0")

# Ordem de empilhamento: o custo operacional e a base esperada; o que vem
# depois e justamente o que costuma passar despercebido.
COMPONENTES_CUSTO = (
    ("custos_operacionais", "Operacionais"),
    ("custo_armazenagem_mp", "Armazenagem de MP"),
    ("custo_armazenagem_produtos", "Armazenagem de produtos"),
    ("perda_pereciveis", "Perda de perecíveis"),
    ("penalidade_sem_submissao", "Penalidade"),
)


def _soma(valores):
    return sum(valores, ZERO)


def _variacao(atual, anterior):
    """Variacao percentual, ou None quando nao ha base de comparacao."""
    if anterior is None or anterior == ZERO:
        return None
    return (atual - anterior) / abs(anterior) * Decimal("100")


def _margem(lucro, receita):
    if not receita:
        return None
    return lucro / receita * Decimal("100")


def _tom(variacao, subir_e_bom=True):
    """Traduz o sinal da variacao em leitura de estado.

    Custo subindo e ruim, receita subindo e boa: o template nao deveria
    precisar saber disso, entao a leitura sai decidida daqui.
    """
    if variacao is None or variacao == ZERO:
        return "mute"
    positiva = variacao > ZERO
    return "ok" if positiva == subir_e_bom else "bad"


def montar_painel(consolidados):
    """Monta o painel financeiro a partir de um queryset ja filtrado.

    `consolidados` deve vir com o escopo de grupo/rodada que a view aplicou.
    Quando o escopo tem mais de um grupo, as series somam a turma inteira.
    """
    registros = list(consolidados)
    if not registros:
        return {"tem_dados": False}

    rodadas = sorted({r.rodada for r in registros})
    por_rodada = {n: [r for r in registros if r.rodada == n] for n in rodadas}

    receita = [_soma(r.receita_vendas for r in por_rodada[n]) for n in rodadas]
    custos = [_soma(r.custos_totais for r in por_rodada[n]) for n in rodadas]
    lucro = [_soma(r.lucro_rodada for r in por_rodada[n]) for n in rodadas]
    market_share = [
        _soma(r.market_share_percent for r in por_rodada[n]) for n in rodadas
    ]

    composicao = [
        {
            "label": rotulo,
            "data": [float(_soma(getattr(r, campo) for r in por_rodada[n])) for n in rodadas],
        }
        for campo, rotulo in COMPONENTES_CUSTO
    ]

    grupos = {}
    for r in registros:
        grupos.setdefault(r.grupo.nome, ZERO)
        grupos[r.grupo.nome] += r.lucro_rodada
    por_grupo = sorted(grupos.items(), key=lambda item: item[1], reverse=True)
    multi_grupo = len(grupos) > 1

    ultima = len(rodadas) - 1
    anterior = ultima - 1 if ultima > 0 else None

    def antes(serie):
        return serie[anterior] if anterior is not None else None

    margem_atual = _margem(lucro[ultima], receita[ultima])
    margem_anterior = (
        _margem(lucro[anterior], receita[anterior]) if anterior is not None else None
    )

    receita_var = _variacao(receita[ultima], antes(receita))
    custos_var = _variacao(custos[ultima], antes(custos))
    lucro_var = _variacao(lucro[ultima], antes(lucro))
    # Participação já é percentual; sua mudança é lida em pontos percentuais,
    # não como uma nova taxa percentual sobre a rodada anterior.
    market_share_var = (
        market_share[ultima] - market_share[anterior]
        if anterior is not None
        else None
    )
    margem_var = (
        margem_atual - margem_anterior
        if margem_atual is not None and margem_anterior is not None
        else None
    )

    kpis = {
        "rodada": rodadas[ultima],
        "rodada_anterior": rodadas[anterior] if anterior is not None else None,
        "receita": receita[ultima],
        "receita_var": receita_var,
        "receita_tom": _tom(receita_var),
        "custos": custos[ultima],
        "custos_var": custos_var,
        "custos_tom": _tom(custos_var, subir_e_bom=False),
        "lucro": lucro[ultima],
        "lucro_var": lucro_var,
        "lucro_tom": _tom(lucro_var),
        "market_share": market_share[ultima],
        "market_share_var": market_share_var,
        "market_share_tom": _tom(market_share_var),
        "margem": margem_atual,
        "margem_var": margem_var,
        "margem_tom": _tom(margem_var),
        "lucro_acumulado": _soma(lucro),
    }

    rotulos = ["Rodada {}".format(n) for n in rodadas]
    graficos = [
        {
            "canvas": "gr-trajetoria",
            "fallback": "fb-trajetoria",
            "type": "bar",
            "labels": rotulos,
            "series": [
                {"label": "Receita", "data": [float(v) for v in receita]},
                {"label": "Custos totais", "data": [float(v) for v in custos]},
                {"label": "Lucro", "data": [float(v) for v in lucro], "type": "line"},
            ],
        },
        {
            "canvas": "gr-composicao",
            "fallback": "fb-composicao",
            "type": "bar",
            "stacked": True,
            "labels": rotulos,
            "series": composicao,
        },
    ]

    if multi_grupo:
        graficos.append(
            {
                "canvas": "gr-grupos",
                "fallback": "fb-grupos",
                "type": "bar",
                "indexAxis": "y",
                # serie unica: o titulo do painel ja a nomeia
                "legenda": False,
                "labels": [nome for nome, _ in por_grupo],
                "series": [
                    {
                        "label": "Lucro acumulado",
                        "data": [float(valor) for _, valor in por_grupo],
                    }
                ],
            }
        )

    return {
        "tem_dados": True,
        "kpis": kpis,
        "graficos": graficos,
        "multi_grupo": multi_grupo,
        "qtd_rodadas": len(rodadas),
        "qtd_grupos": len(grupos),
    }
