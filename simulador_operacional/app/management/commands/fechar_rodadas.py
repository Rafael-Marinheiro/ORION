from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from app.models import Rodada, Grupo, ResultadoFinanceiro

class Command(BaseCommand):
    help = 'Fecha rodadas cujo prazo se encerrou'

    def handle(self, *args, **options):
        agora = timezone.now()
        rodadas = Rodada.objects.filter(fechada=False, fim__lte=agora)
        for rodada in rodadas:
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
