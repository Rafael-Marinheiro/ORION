"""Sorteio do evento da rodada.

Estava implementado duas vezes -- em `views.sortear_evento` e dentro de
`fechar_rodadas` -- com comportamentos que ja divergiam. Fica um so.

O 8.2 define o mecanismo: um evento por rodada, sorteado por probabilidade
constante, com os pesos do 8.4 somando 100%. "Constante" e a palavra que
importa: nao ha cooldown nem bloqueio do evento anterior, porque isso faria
a probabilidade depender do historico. Dois eventos seguidos iguais sao
consequencia legitima de sorteio independente.
"""

import random

from app.models import Evento, EventoRodada


def _filtro_do_jogo(queryset, jogo_id):
    if jogo_id:
        return queryset.filter(jogo_id=jogo_id)
    return queryset.filter(jogo__isnull=True)


def sortear_evento(rodada, jogo_id=None):
    """Evento da rodada, sorteado uma unica vez e reaproveitado depois.

    Devolve o evento ja sorteado se a rodada tiver um, para o sorteio nao
    mudar a cada consulta da tela.
    """
    existente = (
        _filtro_do_jogo(EventoRodada.objects.filter(rodada=rodada), jogo_id)
        .select_related("evento")
        .first()
    )
    if existente:
        return existente.evento

    candidatos = list(Evento.objects.all())
    if not candidatos:
        return None

    pesos = [float(evento.probabilidade or 0) for evento in candidatos]
    if sum(pesos) > 0:
        escolhido = random.choices(candidatos, weights=pesos, k=1)[0]
    else:
        # base sem probabilidade configurada: nao trava o jogo
        escolhido = random.choice(candidatos)

    EventoRodada.objects.create(rodada=rodada, jogo_id=jogo_id, evento=escolhido)
    return escolhido
