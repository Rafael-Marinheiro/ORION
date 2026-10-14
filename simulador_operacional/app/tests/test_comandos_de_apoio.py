# -*- coding: utf-8 -*-
"""Os dois comandos de apoio ao professor.

`seed_turma_demo` monta uma turma completa do zero -- ensaio antes da aula,
ou base limpa depois de auditoria, sem apagar o que ja existe.

`ensaio_de_rede` instrumenta o 11.1: mede a resposta do painel sob a carga
de uma turma e se o fechamento cabe na janela do cron. Nao substitui o
ensaio com alunos reais na rede da instituicao -- so ele mede a rede --,
mas tira a medicao do improviso.
"""

from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from app.models import (
    CapacidadeProdutoGrupo,
    GameConfig,
    Grupo,
    Jogo,
    Rodada,
    User,
)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class SeedTurmaDemoTest(TestCase):
    def _criar(self, **extra):
        saida = StringIO()
        call_command("seed_turma_demo", stdout=saida, **extra)
        return saida.getvalue()

    def test_cria_turma_com_tres_equipes_de_tres_alunos(self):
        self._criar(senha="demo-orion-2026")

        jogo = Jogo.objects.get(nome="Turma Demo")
        self.assertEqual(jogo.grupos.count(), 3)
        for grupo in jogo.grupos.all():
            self.assertEqual(grupo.membros.count(), 3)

    def test_cada_equipe_nasce_com_um_ceo(self):
        """3: o CEO e "o unico autorizado a submeter"."""
        self._criar(senha="demo-orion-2026")

        for grupo in Jogo.objects.get(nome="Turma Demo").grupos.all():
            self.assertIsNotNone(grupo.lider)
            self.assertEqual(grupo.lider.tipo_usuario, "lider_grupo")
            self.assertEqual(
                grupo.membros.filter(tipo_usuario="lider_grupo").count(), 1
            )

    def test_os_recursos_iniciais_saem_da_config_da_turma(self):
        self._criar(senha="demo-orion-2026")

        jogo = Jogo.objects.get(nome="Turma Demo")
        grupo = jogo.grupos.first()
        self.assertEqual(grupo.capital, jogo.config.capital_inicial)
        self.assertEqual(grupo.trabalhadores, jogo.config.trabalhadores_iniciais)
        self.assertEqual(grupo.maquinas, 40)

    def test_o_parque_de_largada_existe_sem_ninguem_abrir_o_painel(self):
        """13.4: o grupo cujo CEO nunca entrou fechava a rodada sem fabrica."""
        self._criar(senha="demo-orion-2026")

        grupo = Jogo.objects.get(nome="Turma Demo").grupos.first()
        self.assertTrue(
            CapacidadeProdutoGrupo.objects.filter(grupo=grupo).exists()
        )

    def test_a_faixa_de_rodadas_do_5_e_respeitada(self):
        saida = StringIO()
        erro = StringIO()
        call_command("seed_turma_demo", rodadas=2, stdout=saida, stderr=erro)

        self.assertIn("3-12", erro.getvalue())
        self.assertFalse(Jogo.objects.filter(nome="Turma Demo").exists())

    def test_nao_sobrescreve_turma_existente_sem_limpar(self):
        self._criar(senha="demo-orion-2026")
        erro = StringIO()

        call_command("seed_turma_demo", stdout=StringIO(), stderr=erro)

        self.assertIn("--limpar", erro.getvalue())
        self.assertEqual(Jogo.objects.filter(nome="Turma Demo").count(), 1)

    def test_limpar_remove_so_a_turma_de_mesmo_nome(self):
        outra = Jogo.objects.create(
            nome="Turma de verdade",
            config=GameConfig.objects.create(numero_rodadas=5),
        )
        intocado = User.objects.create_user(
            email_usuario="nao-mexer@example.com", nome_usuario="Aluno",
            password="senha12345", tipo_usuario="membro_grupo",
        )
        grupo = Grupo.objects.create(nome="Equipe Alheia", jogo=outra)
        grupo.membros.add(intocado)

        self._criar(senha="demo-orion-2026")
        self._criar(senha="demo-orion-2026", limpar=True)

        self.assertTrue(Jogo.objects.filter(nome="Turma de verdade").exists())
        self.assertTrue(User.objects.filter(pk=intocado.pk).exists())
        self.assertEqual(Jogo.objects.filter(nome="Turma Demo").count(), 1)

    def test_abrir_rodada_deixa_a_rodada_1_pronta(self):
        self._criar(senha="demo-orion-2026", abrir_rodada=True)

        jogo = Jogo.objects.get(nome="Turma Demo")
        rodada = Rodada.objects.get(jogo=jogo, numero=1)
        self.assertFalse(rodada.fechada)
        self.assertGreater(rodada.fim, timezone.now())

    def test_sem_senha_informada_o_comando_imprime_a_gerada(self):
        saida = self._criar()

        self.assertIn("senha dos alunos:", saida)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class EnsaioDeRedeTest(TestCase):
    def setUp(self):
        call_command(
            "seed_turma_demo", senha="demo-orion-2026", abrir_rodada=True,
            stdout=StringIO(),
        )
        self.jogo = Jogo.objects.get(nome="Turma Demo")

    def _rodar(self, **extra):
        saida = StringIO()
        call_command("ensaio_de_rede", stdout=saida, stderr=saida, **extra)
        return saida.getvalue()

    def test_mede_o_painel_e_relata_mediana_e_p95(self):
        relatorio = self._rodar(turma="Turma Demo", repeticoes=1)

        self.assertIn("Painel do grupo", relatorio)
        self.assertIn("mediana", relatorio)
        self.assertIn("p95", relatorio)
        self.assertIn("consultas SQL", relatorio)

    def test_relata_se_o_fechamento_cabe_na_janela_do_cron(self):
        relatorio = self._rodar(turma="Turma Demo", repeticoes=1)

        self.assertIn("Fechamento da rodada", relatorio)
        self.assertIn("janela de 1 minuto", relatorio)

    def test_limita_as_equipes_quando_pedido(self):
        relatorio = self._rodar(
            turma="Turma Demo", repeticoes=1, equipes=1
        )

        self.assertIn("1 equipes", relatorio)

    def test_turma_inexistente_nao_quebra(self):
        relatorio = self._rodar(turma="Turma que nao existe")

        self.assertIn("Nenhuma turma encontrada", relatorio)

    def test_sem_rodada_aberta_pula_a_medicao_do_fechamento(self):
        Rodada.objects.filter(jogo=self.jogo).update(fechada=True)

        relatorio = self._rodar(turma="Turma Demo", repeticoes=1)

        self.assertIn("nenhuma rodada aberta", relatorio)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class LimparTurmaComRodadaAbertaTest(TestCase):
    """`--limpar` falhava justamente no caso que o README recomenda.

    `CEOGrupoRodada.usuario` e PROTECT. Apagar o aluno antes da turma
    levantava ProtectedError em toda turma criada com `--abrir-rodada`.
    """

    def test_recria_turma_que_tinha_rodada_aberta(self):
        from app.models import CEOGrupoRodada

        call_command(
            "seed_turma_demo", senha="demo-orion-2026", abrir_rodada=True,
            stdout=StringIO(),
        )
        self.assertTrue(CEOGrupoRodada.objects.exists())

        call_command(
            "seed_turma_demo", senha="demo-orion-2026", abrir_rodada=True,
            limpar=True, stdout=StringIO(),
        )

        self.assertEqual(Jogo.objects.filter(nome="Turma Demo").count(), 1)
        self.assertEqual(
            Jogo.objects.get(nome="Turma Demo").grupos.count(), 3
        )

    def test_nao_deixa_aluno_orfao_para_tras(self):
        call_command(
            "seed_turma_demo", senha="demo-orion-2026", abrir_rodada=True,
            stdout=StringIO(),
        )
        antes = User.objects.filter(email_usuario__endswith="@demo.orion").count()

        call_command(
            "seed_turma_demo", senha="demo-orion-2026", abrir_rodada=True,
            limpar=True, stdout=StringIO(),
        )

        self.assertEqual(
            User.objects.filter(email_usuario__endswith="@demo.orion").count(),
            antes,
        )
