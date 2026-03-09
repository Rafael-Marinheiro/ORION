from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from app.models import Rodada, EventoRodada
from app.views import sortear_eventos

logger = logging.getLogger('agendamentos')

class Command(BaseCommand):
    help = 'Realiza o sorteio de eventos no início de cada rodada'

    def handle(self, *args, **options):
        agora = timezone.now()
        rodadas = Rodada.objects.filter(inicio__lte=agora, fechada=False)
        if not rodadas:
            logger.info('Nenhuma rodada iniciada em %s', agora)
            return
        for rodada in rodadas:
            if EventoRodada.objects.filter(rodada=rodada.numero).exists():
                continue
            eventos = sortear_eventos(rodada.numero)
            if eventos:
                nomes = ', '.join(e.nome for e in eventos)
                logger.info('Sorteados eventos %s para rodada %s', nomes, rodada.numero)
            else:
                logger.info('Nenhum evento disponível para rodada %s', rodada.numero)
