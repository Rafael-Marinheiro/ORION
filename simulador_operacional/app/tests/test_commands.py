import tempfile
from time import perf_counter
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from app.models import (
    ConsolidadoRodadaGrupo,
    Decisao,
    Evento,
    EventoRodada,
    GameConfig,
    Grupo,
    Jogo,
    ResultadoFinanceiro,
    Rodada,
    User,
)


class SortearEventosRodadaCommandTest(TestCase):
    def test_sorteia_por_jogo_sem_repetir_ou_misturar_eventos(self):
        evento = Evento.objects.create(nome="Estabilidade", tipo="demanda", impacto_percentual=0)
        config = GameConfig.objects.create()
        jogos = [Jogo.objects.create(nome=nome, config=config) for nome in ("Turma A", "Turma B")]
        for jogo in [*jogos, None]:
            Rodada.objects.create(jogo=jogo, numero=1, fim=timezone.now() + timezone.timedelta(hours=1))
        EventoRodada.objects.create(jogo=jogos[0], rodada=1, evento=evento)

        call_command("sortear_eventos_rodada")
        call_command("sortear_eventos_rodada")

        self.assertEqual(EventoRodada.objects.count(), 3)
        for jogo in [*jogos, None]:
            self.assertEqual(EventoRodada.objects.filter(jogo=jogo, rodada=1).count(), 1)

    def test_ignora_rodadas_fechadas_e_ainda_nao_iniciadas(self):
        Evento.objects.create(nome="Estabilidade", tipo="demanda", impacto_percentual=0)
        fim = timezone.now() + timezone.timedelta(hours=2)
        Rodada.objects.create(numero=1, fim=fim, fechada=True)
        futura = Rodada.objects.create(numero=2, fim=fim)
        Rodada.objects.filter(pk=futura.pk).update(inicio=fim - timezone.timedelta(hours=1))

        call_command("sortear_eventos_rodada")

        self.assertFalse(EventoRodada.objects.exists())

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


class FechamentoRodadaCapacidadeTest(TestCase):
    def test_fecha_rodada_de_doze_grupos_em_ate_dez_segundos(self):
        """DOCX 3 RF.05: apuração de até 12 grupos em no máximo 10 segundos."""
        Evento.objects.create(nome="Estabilidade", tipo="demanda", impacto_percentual=0)
        Rodada.objects.create(numero=1, fim=timezone.now())
        Grupo.objects.bulk_create(
            [Grupo(nome=f"Equipe {numero}", capital=Decimal("1000000")) for numero in range(1, 13)]
        )

        inicio = perf_counter()
        call_command("fechar_rodadas")
        duracao = perf_counter() - inicio

        self.assertTrue(Rodada.objects.get(numero=1).fechada)
        self.assertEqual(12, Grupo.objects.count())
        self.assertLessEqual(duracao, 10, f"Fechamento levou {duracao:.3f}s")


class FechamentoRodadaPenalidadeTest(TestCase):
    def test_multa_por_ausencia_usa_caixa_do_fim_da_rodada_anterior(self):
        """DOCX 11.2: a multa é 10% do caixa da rodada imediatamente anterior."""
        grupo = Grupo.objects.create(nome="Equipe Ausente", capital=Decimal("100000"))
        ResultadoFinanceiro.objects.create(grupo=grupo, rodada=1, saldo_caixa=Decimal("20000"))
        Rodada.objects.create(numero=2, fim=timezone.now())

        call_command("fechar_rodadas")

        consolidado = ConsolidadoRodadaGrupo.objects.get(grupo=grupo, rodada=2)
        self.assertEqual(consolidado.penalidade_sem_submissao, Decimal("2000"))


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

    def test_lembrete_nao_alcanca_grupo_de_outra_turma(self):
        config = GameConfig.objects.create()
        outra_turma = Jogo.objects.create(nome="Turma B", config=config)
        rodada_da_outra_turma = Rodada.objects.create(
            jogo=outra_turma, numero=1, fim=timezone.now() + timezone.timedelta(minutes=30)
        )
        membro_outra_turma = User.objects.create_user(
            email_usuario="outra@teste.com", nome_usuario="Outra", password="senha123"
        )
        grupo_outra_turma = Grupo.objects.create(nome="G2", jogo=outra_turma, capital=Decimal("100"))
        grupo_outra_turma.membros.add(membro_outra_turma)

        call_command("enviar_lembretes")

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            {tuple(mensagem.to) for mensagem in mail.outbox},
            {("membro@teste.com",), ("outra@teste.com",)},
        )
        self.assertEqual(rodada_da_outra_turma.numero, 1)


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
