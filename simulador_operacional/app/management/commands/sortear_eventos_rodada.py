from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from app.models import Rodada, EventoRodada
from app.services.eventos import sortear_evento

logger = logging.getLogger('agendamentos')

class Command(BaseCommand):
    help = 'Realiza o sorteio de eventos no início de cada rodada'

    def handle(self, *args, **options):
        agora = timezone.now()
        rodadas = Rodada.objects.filter(inicio__lte=agora, fechada=False).order_by("numero", "pk")
        if not rodadas:
            logger.info('Nenhuma rodada iniciada em %s', agora)
            return
        for rodada in rodadas:
            if EventoRodada.objects.filter(jogo_id=rodada.jogo_id, rodada=rodada.numero).exists():
                continue
            evento = sortear_evento(rodada.numero, jogo_id=rodada.jogo_id)
            if evento:
                logger.info('Sorteado evento %s para rodada %s do jogo %s', evento.nome, rodada.numero, rodada.jogo_id)
            else:
                logger.info('Nenhum evento disponível para rodada %s do jogo %s', rodada.numero, rodada.jogo_id)
