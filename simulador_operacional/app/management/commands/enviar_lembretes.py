from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from app.models import Rodada, Grupo, Decisao
import logging

logger = logging.getLogger('agendamentos')

class Command(BaseCommand):
    help = 'Envia lembretes aos grupos sobre o fim das rodadas'

    def handle(self, *args, **options):
        agora = timezone.now()
        limite = agora + timezone.timedelta(hours=1)
        rodadas = Rodada.objects.filter(fechada=False, fim__lte=limite, fim__gt=agora)
        if not rodadas:
            logger.info('Nenhuma rodada proxima do fim em %s', agora)
            return
        for rodada in rodadas:
            grupos = Grupo.objects.all()
            for grupo in grupos:
                if not Decisao.objects.filter(grupo=grupo, rodada=rodada.numero).exists():
                    emails = [m.email_usuario for m in grupo.membros.all()]
                    if not emails:
                        continue
                    send_mail(
                        f'Prazo da rodada {rodada.numero} se encerra em breve',
                        f'Envie suas decisoes ate {rodada.fim}.',
                        None,
                        emails,
                        fail_silently=True,
                    )
                    logger.info('Lembrete enviado para %s na rodada %s', grupo.nome, rodada.numero)
