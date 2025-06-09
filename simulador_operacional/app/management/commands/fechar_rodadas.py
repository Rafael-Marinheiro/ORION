from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from app.models import Rodada, Grupo, ResultadoFinanceiro
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
            for grupo in Grupo.objects.all():
                if not grupo.decisoes.filter(rodada=rodada.numero).exists():
                    penalidade = grupo.capital * Decimal('0.10')
                    grupo.capital -= penalidade
                    grupo.save()
                    rf, _ = ResultadoFinanceiro.objects.get_or_create(
                        grupo=grupo,
                        rodada=rodada.numero,
                    )
                    rf.custos += penalidade
                    rf.saldo_caixa = grupo.capital
                    rf.lucro = rf.receita - rf.custos
                    rf.save()
            rodada.fechada = True
            rodada.save()
            logger.info('Rodada %s fechada', rodada.numero)
