from django.core.management.base import BaseCommand
from django.utils import timezone
from app.models import Rodada
from app.services.fechamento import fechar_rodada
import logging

logger = logging.getLogger('agendamentos')


class Command(BaseCommand):
    help = 'Fecha rodadas cujo prazo se encerrou'

    def handle(self, *args, **options):
        agora = timezone.now()
        rodadas = Rodada.objects.filter(fechada=False, fim__lte=agora)
        if not rodadas:
            logger.info('Nenhuma rodada para fechar em %s', agora)
            self.stdout.write('Nenhuma rodada para fechar')
        for rodada in rodadas:
            logger.info('Fechando rodada %s', rodada.numero)
            self.stdout.write(f'Fechando rodada {rodada.numero}')
            fechar_rodada(rodada.numero)
            logger.info('Rodada %s fechada', rodada.numero)
