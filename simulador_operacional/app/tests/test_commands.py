from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from app.models import Evento, EventoRodada, Rodada


class SortearEventosRodadaCommandTest(TestCase):
    def test_comando_sorteia_evento_para_rodada_aberta(self):
        Evento.objects.create(nome="Greve geral", tipo="greve", impacto_percentual=-10)
        rodada = Rodada.objects.create(numero=1, fim=timezone.now() + timezone.timedelta(hours=1))

        call_command("sortear_eventos_rodada")

        self.assertEqual(EventoRodada.objects.filter(rodada=rodada.numero).count(), 1)

    def test_comando_nao_duplica_evento_ja_sorteado(self):
        evento = Evento.objects.create(nome="Alta do diesel", tipo="custo_transporte", impacto_percentual=15)
        rodada = Rodada.objects.create(numero=1, fim=timezone.now() + timezone.timedelta(hours=1))
        EventoRodada.objects.create(rodada=rodada.numero, evento=evento)

        call_command("sortear_eventos_rodada")

        self.assertEqual(EventoRodada.objects.filter(rodada=rodada.numero).count(), 1)
