# -*- coding: utf-8 -*-
"""A caixa de sugestoes grava uma linha no roadmap do projeto.

Estava aberta: qualquer visitante podia acrescentar texto a um arquivo do
servidor, sem limite de envios e sem deixar quem foi. E o campo aceitava
quebras de linha, que no markdown viram varios itens -- uma lista forjada
num envio so.

O arquivo tambem era escrito por uma funcao de teste no estilo pytest, que
o runner do Django nao coleta: a tela nunca foi exercitada pela suite.
"""

from django.test import TestCase, override_settings
from django.urls import reverse

from app.models import User


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class FeedbackTest(TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path

        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.roadmap = Path(self.pasta.name) / "roadmap.md"
        self.aluno = User.objects.create_user(
            email_usuario="aluno-feedback@example.com", nome_usuario="Aluno",
            password="senha12345", tipo_usuario="membro_grupo",
        )

    def test_visitante_sem_login_nao_escreve_no_roadmap(self):
        with override_settings(ROADMAP_FILE=self.roadmap):
            resposta = self.client.post(
                reverse("feedback"), {"suggestion": "Spam de fora"}
            )

        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("login"), resposta["Location"])
        self.assertFalse(self.roadmap.exists())

    def test_aluno_logado_envia_sugestao(self):
        self.client.force_login(self.aluno)

        with override_settings(ROADMAP_FILE=self.roadmap):
            resposta = self.client.post(
                reverse("feedback"),
                {"suggestion": "Nova ideia", "email": "a@b.com"},
            )

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(
            self.roadmap.read_text(encoding="utf-8").startswith("- Nova ideia")
        )

    def test_quebra_de_linha_nao_vira_varios_itens_do_roadmap(self):
        self.client.force_login(self.aluno)

        with override_settings(ROADMAP_FILE=self.roadmap):
            self.client.post(
                reverse("feedback"),
                {"suggestion": "Primeira\n- Item forjado\n- Outro forjado"},
            )

        linhas = self.roadmap.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(linhas), 1)
        self.assertIn("Primeira - Item forjado - Outro forjado", linhas[0])
