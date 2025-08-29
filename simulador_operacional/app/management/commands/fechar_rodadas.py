from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from app.models import Rodada, Grupo, ResultadoFinanceiro, EventoRodada, Produto
from app.services.penalidade_service import aplicar_penalidade
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
            eventos = [er.evento for er in EventoRodada.objects.filter(rodada=rodada.numero)]
            greve_ativa = any(e.tipo == 'greve' for e in eventos)
            perdas = [e for e in eventos if e.tipo == 'perda_estoque']
            for grupo in Grupo.objects.all():
                if not grupo.decisoes.filter(rodada=rodada.numero).exists():
                    if greve_ativa:
                        ultima = grupo.decisoes.order_by('-rodada').first()
                        if ultima:
                            ultima.pk = None
                            ultima.rodada = rodada.numero
                            ultima.quantidade = 0
                            ultima.resultado = 'Decisão replicada automaticamente (greve)'
                            ultima.save()
                    else:
                        penalidade = grupo.capital * Decimal('0.10')
                        aplicar_penalidade(grupo, rodada.numero, penalidade)

                        ultima = grupo.decisoes.order_by('-rodada').first()
                        if ultima:
                            ultima.pk = None
                            ultima.rodada = rodada.numero
                            ultima.resultado = 'Decisão replicada automaticamente'
                            ultima.save()
                for evento in perdas:
                    perda = int(grupo.estoque * evento.impacto_percentual / 100)
                    if perda:
                        grupo.estoque -= perda
                if perdas:
                    grupo.save()
                # Remove produtos vencidos e calcula custo de armazenagem
                produtos = Produto.objects.filter(grupo=grupo)
                removidos = 0
                for prod in produtos:
                    if prod.esta_vencido():
                        removidos += prod.quantidade
                        prod.quantidade = 0
                        prod.save()
                if removidos:
                    grupo.estoque = max(grupo.estoque - removidos, 0)
                    grupo.save()

                custo_armazenagem = Decimal("0")
                for prod in produtos:
                    custo_armazenagem += prod.custo_armazenagem()
                if custo_armazenagem:
                    grupo.capital -= custo_armazenagem
                    grupo.save()
                    rf, _ = ResultadoFinanceiro.objects.get_or_create(
                        grupo=grupo,
                        rodada=rodada.numero,
                    )
                    rf.custos += custo_armazenagem
                    rf.saldo_caixa = grupo.capital
                    rf.lucro = rf.receita - rf.custos
                    rf.save()
            rodada.fechada = True
            rodada.save()
            logger.info('Rodada %s fechada', rodada.numero)
