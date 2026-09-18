import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from app.models import Decisao, Evento, EventoRodada, Grupo, Rodada, User


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


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EnviarLembretesCommandTest(TestCase):
    def setUp(self):
        self.rodada = Rodada.objects.create(
            numero=1, fim=timezone.now() + timezone.timedelta(minutes=30)
        )
        self.grupo = Grupo.objects.create(nome="G1", capital=Decimal("100"))
        self.membro = User.objects.create_user(
            email_usuario="membro@teste.com", nome_usuario="Membro", password="senha123"
        )
        self.grupo.membros.add(self.membro)
        mail.outbox = []

    def test_envia_lembrete_para_grupo_sem_decisao(self):
        call_command("enviar_lembretes")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["membro@teste.com"])
        self.assertIn(str(self.rodada.numero), mail.outbox[0].subject)

    def test_nao_envia_lembrete_quando_grupo_ja_decidiu(self):
        Decisao.objects.create(grupo=self.grupo, rodada=self.rodada.numero)

        call_command("enviar_lembretes")

        self.assertEqual(len(mail.outbox), 0)


class BackupDbCommandTest(TestCase):
    def test_copia_arquivo_do_banco_para_pasta_de_backups(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            origem = Path(temp_dir) / "db.sqlite3"
            origem.write_bytes(b"conteudo-do-banco")
            destino = Path(temp_dir) / "base"

            with override_settings(BASE_DIR=destino), patch.dict(
                settings.DATABASES["default"], {"NAME": str(origem)}
            ):
                call_command("backupdb")

            copias = list((destino / "backups").glob("db_*.sqlite3"))
            self.assertEqual(len(copias), 1)
            self.assertEqual(copias[0].read_bytes(), b"conteudo-do-banco")
