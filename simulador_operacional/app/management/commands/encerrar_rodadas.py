from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import Rodada


class Command(BaseCommand):
    help = "Fecha automaticamente as rodadas cujo prazo expirou"

    def handle(self, *args, **options):
        agora = timezone.now()
        rodadas = Rodada.objects.filter(encerrada=False, data_fim__lte=agora)
        if not rodadas:
            self.stdout.write("Nenhuma rodada para encerrar")
        for rodada in rodadas:
            rodada.encerrar()
            self.stdout.write(self.style.SUCCESS(f"Rodada {rodada.numero} encerrada"))

