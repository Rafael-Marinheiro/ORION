from django.core.management.base import BaseCommand
from app.models import RandomEvent, EventHistory
import random

class Command(BaseCommand):
    help = "Sorteia e aplica eventos aleatórios"

    def add_arguments(self, parser):
        parser.add_argument('--rodada', type=int, default=1)

    def handle(self, *args, **options):
        rodada = options['rodada']
        for event in RandomEvent.objects.all():
            if random.random() < float(event.probabilidade):
                EventHistory.objects.create(evento=event, rodada=rodada)
                self.stdout.write(self.style.SUCCESS(f"Evento aplicado: {event.descricao}"))

