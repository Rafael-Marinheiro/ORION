# -*- coding: utf-8 -*-
"""15.4 -- Avaliacao do Simulador.

O documento pede questionario "com itens em escala Likert e campos
abertos", aplicado "ao final do ciclo do jogo", mais o questionario do
docente e os relatorios de uso. O sistema tinha apenas `/feedback/`, caixa
de sugestao livre: nao e questionario, nao tem escala e nao produz dado
comparavel entre turmas.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import (
    AvaliacaoSimulador,
    ConsolidadoRodadaGrupo,
    Decisao,
    GameConfig,
    Grupo,
    Jogo,
    Rodada,
    User,
)
from app.services.avaliacao import (
    ITENS_ALUNO,
    ITENS_DOCENTE,
    chaves_do_papel,
    ciclo_encerrado,
    consolidar_respostas,
    indicadores_de_uso,
)


def _respostas(papel):
    return {chave: "4" for chave in chaves_do_papel(papel)}


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class QuestionarioDoAlunoTest(TestCase):
    def setUp(self):
        self.config = GameConfig.objects.create(numero_rodadas=2)
        self.jogo = Jogo.objects.create(nome="Turma A", config=self.config)
        self.grupo = Grupo.objects.create(nome="Equipe Vega", jogo=self.jogo)
        self.aluno = User.objects.create_user(
            email_usuario="aluno-av@example.com", nome_usuario="Aluno",
            password="senha12345", tipo_usuario="membro_grupo",
        )
        self.grupo.membros.add(self.aluno)
        self.client.force_login(self.aluno)

    def _fechar_o_ciclo(self):
        for numero in (1, 2):
            Rodada.objects.create(
                jogo=self.jogo, numero=numero,
                fim=timezone.now() - timedelta(hours=1), fechada=True,
            )

    def test_antes_do_fim_do_ciclo_o_questionario_nao_abre(self):
        """15.4: "questionarios aplicados ao final do ciclo do jogo"."""
        Rodada.objects.create(
            jogo=self.jogo, numero=1,
            fim=timezone.now() + timedelta(hours=1),
        )

        resposta = self.client.get(reverse("avaliacao"))

        self.assertFalse(resposta.context["liberado"])
        self.assertContains(resposta, "quando a última rodada do ciclo fechar")

    def test_com_o_ciclo_fechado_o_questionario_abre(self):
        self._fechar_o_ciclo()

        resposta = self.client.get(reverse("avaliacao"))

        self.assertTrue(resposta.context["liberado"])
        self.assertEqual(resposta.context["papel"], "aluno")

    def test_os_quatro_temas_do_15_4_a_estao_no_questionario(self):
        self._fechar_o_ciclo()

        corpo = self.client.get(reverse("avaliacao")).content.decode()

        for _, titulo, _ in ITENS_ALUNO:
            self.assertIn(titulo, corpo, titulo)
        self.assertIn("Sugestões de melhoria", corpo)

    def test_a_escala_tem_cinco_pontos(self):
        self._fechar_o_ciclo()

        form = self.client.get(reverse("avaliacao")).context["form"]

        primeiro = chaves_do_papel("aluno")[0]
        self.assertEqual(len(form.fields[primeiro].choices), 5)

    def test_o_envio_grava_escala_e_texto(self):
        self._fechar_o_ciclo()
        dados = _respostas("aluno")
        dados["aberta_melhoria"] = "Mais tempo entre rodadas."

        self.client.post(reverse("avaliacao"), dados)

        avaliacao = AvaliacaoSimulador.objects.get(usuario=self.aluno)
        self.assertEqual(avaliacao.papel, "aluno")
        self.assertEqual(avaliacao.jogo, self.jogo)
        self.assertEqual(avaliacao.respostas["u1"], 4)
        self.assertEqual(
            avaliacao.comentarios["melhoria"], "Mais tempo entre rodadas."
        )

    def test_item_da_escala_em_branco_recusa_o_envio(self):
        self._fechar_o_ciclo()
        dados = _respostas("aluno")
        del dados["u1"]

        resposta = self.client.post(reverse("avaliacao"), dados)

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(AvaliacaoSimulador.objects.exists())

    def test_campo_aberto_em_branco_e_aceito(self):
        self._fechar_o_ciclo()

        self.client.post(reverse("avaliacao"), _respostas("aluno"))

        self.assertTrue(AvaliacaoSimulador.objects.exists())

    def test_responder_de_novo_substitui_em_vez_de_duplicar(self):
        self._fechar_o_ciclo()
        self.client.post(reverse("avaliacao"), _respostas("aluno"))

        dados = _respostas("aluno")
        dados["u1"] = "2"
        self.client.post(reverse("avaliacao"), dados)

        self.assertEqual(AvaliacaoSimulador.objects.count(), 1)
        self.assertEqual(
            AvaliacaoSimulador.objects.get().respostas["u1"], 2
        )

    def test_o_envio_antes_do_fim_do_ciclo_e_recusado(self):
        Rodada.objects.create(
            jogo=self.jogo, numero=1, fim=timezone.now() + timedelta(hours=1)
        )

        self.client.post(reverse("avaliacao"), _respostas("aluno"))

        self.assertFalse(AvaliacaoSimulador.objects.exists())


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class QuestionarioDoDocenteTest(TestCase):
    def setUp(self):
        self.config = GameConfig.objects.create(numero_rodadas=2)
        self.jogo = Jogo.objects.create(nome="Turma A", config=self.config)
        Rodada.objects.create(
            jogo=self.jogo, numero=1, fim=timezone.now() + timedelta(hours=1)
        )
        self.professor = User.objects.create_user(
            email_usuario="prof-av@example.com", nome_usuario="Professora",
            password="senha12345", tipo_usuario="gamemaster",
        )
        self.client.force_login(self.professor)

    def test_o_docente_responde_sem_esperar_o_ciclo_fechar(self):
        """Ele acompanha o ciclo inteiro e registra observacao durante."""
        resposta = self.client.get(reverse("avaliacao"))

        self.assertEqual(resposta.context["papel"], "docente")
        self.assertTrue(resposta.context["liberado"])

    def test_os_tres_temas_do_15_4_b_estao_no_questionario(self):
        corpo = self.client.get(reverse("avaliacao")).content.decode()

        for _, titulo, _ in ITENS_DOCENTE:
            self.assertIn(titulo, corpo, titulo)
        self.assertIn("comportamento e o desempenho dos grupos", corpo)

    def test_o_envio_do_docente_e_marcado_como_docente(self):
        dados = _respostas("docente")
        dados["aberta_grupos"] = "A Vega planejou melhor a compra."

        self.client.post(reverse("avaliacao"), dados)

        avaliacao = AvaliacaoSimulador.objects.get(usuario=self.professor)
        self.assertEqual(avaliacao.papel, "docente")
        self.assertIn("Vega", avaliacao.comentarios["grupos"])


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class ConsolidacaoTest(TestCase):
    def test_a_media_e_a_distribuicao_saem_por_item(self):
        jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=2)
        )
        for indice, nota in enumerate([5, 3, 1]):
            usuario = User.objects.create_user(
                email_usuario=f"a{indice}@example.com", nome_usuario=f"A{indice}",
                password="senha12345", tipo_usuario="membro_grupo",
            )
            AvaliacaoSimulador.objects.create(
                usuario=usuario, jogo=jogo, papel="aluno",
                respostas={**{c: 4 for c in chaves_do_papel("aluno")}, "u1": nota},
            )

        blocos = consolidar_respostas(
            list(AvaliacaoSimulador.objects.all()), "aluno"
        )

        u1 = blocos[0]["linhas"][0]
        self.assertEqual(u1["n"], 3)
        self.assertEqual(u1["media"], 3.0)
        # distribuicao expoe a polarizacao que a media esconde
        self.assertEqual(u1["distribuicao"], [1, 0, 1, 0, 1])


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class IndicadoresDeUsoTest(TestCase):
    """15.4.c -- rodadas realizadas, participacao, submissoes em tempo,
    consistencia e variacao entre desempenhos."""

    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=2)
        )
        for numero in (1, 2):
            Rodada.objects.create(
                jogo=self.jogo, numero=numero,
                fim=timezone.now() - timedelta(hours=1), fechada=True,
            )
        self.assidua = Grupo.objects.create(nome="Equipe Assídua", jogo=self.jogo)
        self.ausente = Grupo.objects.create(nome="Equipe Ausente", jogo=self.jogo)

        for numero in (1, 2):
            Decisao.objects.create(
                grupo=self.assidua, rodada=numero, descricao=f"Rodada {numero}"
            )
            ConsolidadoRodadaGrupo.objects.create(
                grupo=self.assidua, rodada=numero, total_ofertado=100,
                score_multicriterio=Decimal("80"),
            )
        # a ausente submeteu uma rodada, e sem operar
        Decisao.objects.create(grupo=self.ausente, rodada=1, descricao="Rodada 1")
        ConsolidadoRodadaGrupo.objects.create(
            grupo=self.ausente, rodada=1, total_ofertado=0,
            score_multicriterio=Decimal("40"),
        )

    def test_conta_as_rodadas_realizadas(self):
        indicadores = indicadores_de_uso(self.jogo)

        self.assertEqual(indicadores["rodadas_realizadas"], 2)
        self.assertEqual(indicadores["rodadas_previstas"], 2)

    def test_participacao_por_grupo(self):
        indicadores = indicadores_de_uso(self.jogo)

        por_nome = {p["grupo"].nome: p for p in indicadores["participacao"]}
        self.assertEqual(por_nome["Equipe Assídua"]["participacao_percent"], 100.0)
        self.assertEqual(por_nome["Equipe Ausente"]["participacao_percent"], 50.0)

    def test_consistencia_separa_quem_submeteu_sem_decidir(self):
        """11.2: submeter sem decidir repete a rodada anterior."""
        indicadores = indicadores_de_uso(self.jogo)

        por_nome = {p["grupo"].nome: p for p in indicadores["participacao"]}
        self.assertEqual(por_nome["Equipe Assídua"]["consistencia_percent"], 100.0)
        self.assertEqual(por_nome["Equipe Ausente"]["consistencia_percent"], 0.0)

    def test_variacao_entre_desempenhos(self):
        indicadores = indicadores_de_uso(self.jogo)

        self.assertEqual(indicadores["desempenho_menor"], 40.0)
        self.assertEqual(indicadores["desempenho_maior"], 80.0)
        self.assertEqual(indicadores["desempenho_desvio"], 20.0)

    def test_submissoes_em_tempo_sobre_o_possivel(self):
        indicadores = indicadores_de_uso(self.jogo)

        self.assertEqual(indicadores["submissoes_em_tempo"], 3)
        self.assertEqual(indicadores["submissoes_possiveis"], 4)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RelatorioDaAvaliacaoTest(TestCase):
    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=2)
        )
        Rodada.objects.create(
            jogo=self.jogo, numero=1,
            fim=timezone.now() - timedelta(hours=1), fechada=True,
        )
        self.professor = User.objects.create_user(
            email_usuario="prof-rel@example.com", nome_usuario="Professora",
            password="senha12345", tipo_usuario="gamemaster",
        )

    def test_o_aluno_nao_abre_o_consolidado(self):
        aluno = User.objects.create_user(
            email_usuario="aluno-rel@example.com", nome_usuario="Aluno",
            password="senha12345", tipo_usuario="membro_grupo",
        )
        self.client.force_login(aluno)

        resposta = self.client.get(reverse("avaliacao_relatorio"))

        self.assertIn(resposta.status_code, (302, 403))

    def test_o_relatorio_mostra_respostas_e_indicadores(self):
        aluno = User.objects.create_user(
            email_usuario="aluno-rel2@example.com", nome_usuario="Aluno",
            password="senha12345", tipo_usuario="membro_grupo",
        )
        AvaliacaoSimulador.objects.create(
            usuario=aluno, jogo=self.jogo, papel="aluno",
            respostas={c: 5 for c in chaves_do_papel("aluno")},
            comentarios={"melhoria": "Mais tempo entre rodadas."},
        )
        self.client.force_login(self.professor)

        resposta = self.client.get(
            reverse("avaliacao_relatorio"), {"jogo": self.jogo.id}
        )

        self.assertEqual(resposta.context["total_alunos"], 1)
        self.assertContains(resposta, "Mais tempo entre rodadas.")
        self.assertContains(resposta, "Indicadores de uso")

    def test_turma_sem_resposta_diz_isso(self):
        self.client.force_login(self.professor)

        resposta = self.client.get(
            reverse("avaliacao_relatorio"), {"jogo": self.jogo.id}
        )

        self.assertContains(resposta, "Nenhuma resposta de aluno")


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class CicloEncerradoTest(TestCase):
    def test_falta_uma_rodada_e_o_ciclo_nao_esta_encerrado(self):
        jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=3)
        )
        for numero in (1, 2):
            Rodada.objects.create(
                jogo=jogo, numero=numero,
                fim=timezone.now() - timedelta(hours=1), fechada=True,
            )

        self.assertFalse(ciclo_encerrado(jogo))

    def test_todas_fechadas_encerra_o_ciclo(self):
        jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=2)
        )
        for numero in (1, 2):
            Rodada.objects.create(
                jogo=jogo, numero=numero,
                fim=timezone.now() - timedelta(hours=1), fechada=True,
            )

        self.assertTrue(ciclo_encerrado(jogo))
