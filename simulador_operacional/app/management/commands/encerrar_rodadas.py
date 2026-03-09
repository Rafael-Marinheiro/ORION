from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Alias legado para fechar_rodadas. Mantido por compatibilidade."

    def handle(self, *args, **options):
        self.stdout.write("Executando fechamento via comando fechar_rodadas...")
        call_command("fechar_rodadas")
