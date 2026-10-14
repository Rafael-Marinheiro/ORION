"""Sorteio do evento da rodada.

Estava implementado duas vezes -- em `views.sortear_evento` e dentro de
`fechar_rodadas` -- com comportamentos que ja divergiam. Fica um so.

Politica de sorteio (decisao de 14/10/2026)
-------------------------------------------
Todos os eventos elegiveis tem a MESMA chance, e o que saiu entra em
cooldown por algumas rodadas. Antes o sorteio usava os pesos do 8.4 e
apenas penalizava o evento recente, para nao achatar pesos distintos --
objecao que deixou de existir quando os pesos passaram a ser iguais.

A coluna `probabilidade` continua gravada com o valor do 8.4: o banco
segue fiel ao documento, e o que mudou foi a politica. Voltar atras e
trocar um parametro, nao migrar dado.

PENDENTE DE RATIFICACAO do autor da especificacao: o 8.4 define
probabilidades distintas.
"""

import random
from decimal import Decimal

from app.models import Evento, EventoRodada, Rodada
from app.parametros import (
    CHANCE_EVENTO_DUPLO,
    COOLDOWN_EVENTO_RODADAS,
    MAXIMO_EVENTOS_POR_RODADA,
)


def _filtro_do_jogo(queryset, jogo_id):
    if jogo_id:
        return queryset.filter(jogo_id=jogo_id)
    return queryset.filter(jogo__isnull=True)


def _pool_estendido(jogo_id):
    """A turma sorteia alem da tabela do 8.4?

    Padrao e nao: sem configuracao explicita, o sorteio e exatamente o do
    documento. Grupos sem turma usam a configuracao avulsa.
    """
    from app.models import GameConfig, Jogo

    if jogo_id:
        jogo = Jogo.objects.filter(id=jogo_id).select_related("config").first()
        return bool(jogo and jogo.config and jogo.config.eventos_estendidos)
    avulsa = GameConfig.objects.filter(id=1).first()
    return bool(avulsa and avulsa.eventos_estendidos)


def _em_cooldown(rodada, jogo_id):
    """Eventos que sairam ha poucas rodadas e estao bloqueados.

    A distancia sai da rodada corrente, nao da ultima rodada com evento:
    com lacuna -- rodada sem sorteio -- medir pela ultima registrada
    bloquearia um evento que ja e antigo.
    """
    if COOLDOWN_EVENTO_RODADAS <= 0:
        return set()
    anteriores = _filtro_do_jogo(
        EventoRodada.objects.filter(
            rodada__lt=rodada, rodada__gte=rodada - COOLDOWN_EVENTO_RODADAS
        ),
        jogo_id,
    )
    return set(anteriores.values_list("evento_id", flat=True))


def _ja_usados_no_jogo(jogo_id):
    """Eventos marcados como `unico_por_jogo` que ja aconteceram.

    O surto de gripe e o caso: a oferta de imunizacao perde o sentido na
    segunda vez, porque a equipe ja sabe o preco e o efeito exatos.
    """
    usados = _filtro_do_jogo(EventoRodada.objects.all(), jogo_id).filter(
        evento__unico_por_jogo=True
    )
    return set(usados.values_list("evento_id", flat=True))


def sortear_evento(rodada, jogo_id=None):
    """Evento da rodada, sorteado uma unica vez e reaproveitado depois.

    Devolve o evento ja sorteado se a rodada tiver um, para o sorteio nao
    mudar a cada consulta da tela.
    """
    existente = (
        _filtro_do_jogo(
            EventoRodada.objects.filter(rodada=rodada, manual=False), jogo_id
        )
        .select_related("evento")
        .first()
    )
    if existente:
        return existente.evento

    # O professor pode ter determinado o evento da rodada e dispensado o
    # sorteio: sem isto, a turma receberia dois.
    escolhida = _filtro_do_jogo(Rodada.objects.filter(numero=rodada), jogo_id).first()
    if escolhida and not escolhida.sorteio_evento:
        return None

    # O evento manual do professor nao entra no sorteio: ele acontece
    # porque foi mandado, nao por peso. E o que ele ja escolheu a dedo sai
    # do sorteio desta rodada -- repetir o mesmo evento seria anunciar duas
    # vezes a mesma noticia, e a rodada so aceita cada evento uma vez.
    ja_na_rodada = set(
        _filtro_do_jogo(EventoRodada.objects.filter(rodada=rodada), jogo_id)
        .values_list("evento_id", flat=True)
    )
    escolhido = _sortear_um(rodada, jogo_id, ja_na_rodada)
    if escolhido is None:
        return None
    EventoRodada.objects.create(
        rodada=rodada, jogo_id=jogo_id, evento=escolhido, manual=False
    )

    # RN-10: "ate 2 eventos aleatorios simultaneos". A rodada sai com dois
    # em 30% das vezes -- e nunca passa de dois no total, contando o que o
    # professor marcou na abertura.
    total_na_rodada = len(ja_na_rodada) + 1
    if (
        total_na_rodada < MAXIMO_EVENTOS_POR_RODADA
        and random.random() < CHANCE_EVENTO_DUPLO
    ):
        segundo = _sortear_um(
            rodada, jogo_id, ja_na_rodada | {escolhido.id}
        )
        if segundo is not None:
            EventoRodada.objects.create(
                rodada=rodada, jogo_id=jogo_id, evento=segundo, manual=False
            )
    return escolhido


def _sortear_um(rodada, jogo_id, excluidos):
    """Um evento elegivel, com todos tendo a mesma chance.

    Fora do sorteio ficam: o evento manual (acontece porque foi mandado),
    o que ja esta na rodada, o que saiu ha poucas rodadas (cooldown) e o
    `unico_por_jogo` que ja aconteceu nesta turma.
    """
    disponiveis = Evento.objects.filter(manual=False)
    if not _pool_estendido(jogo_id):
        disponiveis = disponiveis.filter(extensao=False)

    bloqueados = (
        set(excluidos)
        | _em_cooldown(rodada, jogo_id)
        | _ja_usados_no_jogo(jogo_id)
    )
    candidatos = [e for e in disponiveis if e.id not in bloqueados]

    if not candidatos:
        # Cooldown apertado demais para o tamanho do pool: solta o cooldown
        # antes de deixar a rodada sem evento, porque o 8.2 garante que
        # "sempre haja um evento ativo".
        candidatos = [
            e
            for e in disponiveis
            if e.id not in set(excluidos) | _ja_usados_no_jogo(jogo_id)
        ]
    if not candidatos:
        return None
    return random.choice(candidatos)


def eventos_da_rodada(rodada, jogo_id=None):
    """Todos os eventos vigentes na rodada -- o sorteado e o do professor.

    Ate 25/09/2026 era sempre um so (8.2). O professor pode agora somar um
    evento manual ao sorteado; esta e a lista que o fechamento aplica.

    `duracao_rodadas` vale para qualquer modo, nao so para os de estado. O
    8.2 ressalva "com reversao automatica dos impactos na rodada seguinte
    (salvo eventos recorrentes)": o evento recorrente estava previsto no
    documento e no modelo, mas um evento percentual de tres rodadas durava
    uma -- a lista so trazia o que fora sorteado NESTA rodada.
    """
    alcance = _filtro_do_jogo(
        EventoRodada.objects.filter(rodada__lte=rodada), jogo_id
    ).select_related("evento")
    vigentes = [
        evento_rodada
        for evento_rodada in alcance
        if rodada
        <= evento_rodada.rodada + max(evento_rodada.evento.duracao_rodadas, 1) - 1
    ]
    vigentes.sort(key=lambda er: (er.manual, er.id))
    return [evento_rodada.evento for evento_rodada in vigentes]


def _atinge(evento, cidade_id):
    """Evento sem praca marcada vale para o mercado inteiro (8.4)."""
    if cidade_id is None:
        return True
    marcadas = list(evento.cidades.values_list("id", flat=True))
    return not marcadas or cidade_id in marcadas


def fator_percentual(eventos, tipo, cidade_id=None):
    """Multiplicador acumulado dos eventos percentuais daquele tipo.

    Dois eventos que encarecem a producao encarecem as duas vezes: os
    efeitos se compoem, nao se substituem.
    """
    fator = Decimal("1")
    for evento in eventos or ():
        if (
            evento
            and evento.modo_aplicacao == "percentual"
            and evento.tipo == tipo
            and _atinge(evento, cidade_id)
        ):
            fator *= Decimal("1") + Decimal(evento.impacto_percentual) / Decimal("100")
    return fator


def efeito_absoluto(eventos, tipo, cidade_id=None):
    """Soma dos efeitos em valor absoluto daquele tipo.

    O 8.4 so trabalha com percentual; o absoluto existe para o evento que o
    professor cria -- "a demanda de Recife cai 500 unidades".
    """
    total = Decimal("0")
    for evento in eventos or ():
        if (
            evento
            and evento.modo_aplicacao == "absoluto"
            and evento.tipo == tipo
            and _atinge(evento, cidade_id)
        ):
            total += Decimal(evento.valor_absoluto or 0)
    return total


def lista_de_eventos(eventos=None, evento=None):
    """Normaliza os dois jeitos de receber evento.

    As funcoes do fechamento recebiam um evento so. Continuam aceitando,
    para nao reescrever chamada por chamada o que ja funciona.
    """
    todos = list(eventos or ())
    if evento is not None and evento not in todos:
        todos.append(evento)
    return todos


def evento_estado_ativo(rodada_numero, efeito_estado, jogo_id=None):
    """Evento de estado ainda vigente na rodada, se houver.

    Estava escrito duas vezes -- em `views.evento_estado_ativo` e em
    `fechar_rodadas.obter_evento_estado_ativo` -- com o mesmo corpo. Fica um
    so, pelo mesmo motivo que o sorteio ficou.
    """
    eventos_rodada = _filtro_do_jogo(
        EventoRodada.objects.filter(rodada__lte=rodada_numero), jogo_id
    ).select_related("evento")

    for evento_rodada in eventos_rodada.order_by("-rodada"):
        evento = evento_rodada.evento
        if evento.modo_aplicacao != "estado" or evento.efeito_estado != efeito_estado:
            continue
        fim_vigencia = evento_rodada.rodada + max(evento.duracao_rodadas, 1) - 1
        if rodada_numero <= fim_vigencia:
            return evento
    return None


# --------------------------------------------------------------------------
# Eventos de decisao
#
# Ate aqui todo evento era passivo: sorteia, aplica igual para todos,
# calcula. O evento de decisao faz uma oferta -- a mesma para todas as
# equipes -- e o resultado depende da resposta de cada uma.
#
# Isto contraria a letra do 8.2 ("o evento sorteado afeta todos os grupos de
# maneira igual") e usa variaveis que o 8.3 nao lista (forca de trabalho e
# caixa). A oferta e uniforme; a consequencia e da gestao. Pendente de
# ratificacao do autor da especificacao.
# --------------------------------------------------------------------------

def evento_de_decisao(rodada, jogo_id=None):
    """A oferta vigente na rodada, se houver."""
    for evento in eventos_da_rodada(rodada, jogo_id):
        if evento.modo_aplicacao == "decisao":
            return evento
    return None


def custo_da_oferta(evento, grupo):
    """Preco por trabalhador vezes a equipe: quem investiu em pessoal paga
    mais, e a decisao deixa de ser taxa fixa."""
    unitario = Decimal(evento.custo_unitario_decisao or 0)
    return (unitario * Decimal(grupo.trabalhadores or 0)).quantize(Decimal("0.01"))


def registrar_decisao(grupo, rodada, evento, aceitou):
    """Resposta da equipe. Nao cobra nada: o debito e do fechamento."""
    from app.models import DecisaoEventoGrupo

    decisao, _ = DecisaoEventoGrupo.objects.update_or_create(
        grupo=grupo, rodada=rodada, evento=evento,
        defaults={"aceitou": bool(aceitou)},
    )
    return decisao


def resolver_decisao(grupo, rodada, evento):
    """Fecha a decisao da equipe e devolve (custo, percentual_afetado).

    Chamada uma vez por grupo no fechamento. Quem nao respondeu recebe a
    linha aqui, como recusa -- nao pagou. O sorteio do afastamento acontece
    neste momento e fica gravado, para o numero nao mudar depois.
    """
    from app.models import DecisaoEventoGrupo

    decisao = DecisaoEventoGrupo.objects.filter(
        grupo=grupo, rodada=rodada, evento=evento
    ).first()
    if decisao is None:
        decisao = DecisaoEventoGrupo.objects.create(
            grupo=grupo, rodada=rodada, evento=evento, aceitou=False
        )
    if decisao.custo or decisao.afetados_percent:
        return decisao.custo, decisao.afetados_percent

    if decisao.aceitou:
        decisao.custo = custo_da_oferta(evento, grupo)
        decisao.afetados_percent = 0
    else:
        # Valor unico, igual para todas as equipes que recusarem.
        #
        # A primeira versao sorteava numa faixa, para que recusar fosse
        # aposta. O Product Owner decidiu o contrario, e com razao: o jogo
        # precisa ser simetrico, e duas equipes que tomam a MESMA decisao
        # nao podem terminar a rodada com perdas diferentes por sorte. Isso
        # tambem aproxima o evento da letra do 8.2 -- "afeta todos os grupos
        # de maneira igual" --, que a faixa esticava.
        decisao.custo = Decimal("0")
        decisao.afetados_percent = int(evento.impacto_percentual or 0)
    decisao.save(update_fields=["custo", "afetados_percent"])
    return decisao.custo, decisao.afetados_percent


def fracao_de_operadores(grupo, rodada):
    """Parcela da equipe disponivel na rodada, ja decidida no fechamento."""
    from app.models import DecisaoEventoGrupo

    afastados = 0
    for decisao in DecisaoEventoGrupo.objects.filter(grupo=grupo, rodada=rodada):
        if decisao.evento.efeito_estado == "afastamento_equipe":
            afastados = max(afastados, int(decisao.afetados_percent or 0))
    return max(0.0, 1.0 - afastados / 100.0)
