"""Ensaio HTTP + banco real de teste: professor, duas equipes, três rodadas.

Regras: DOCX 3 RF.01–05; DOCX 5 RN-01–03; DOCX 7 §7.2 (D+1);
DOCX 9 §9.2; DOCX 11 (fechamento); guia D9 e base regional validada.
Somente relógio e sorteio são controlados; operações passam pelas views.
"""

from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import (
    AuditoriaSubmissaoRodada, CapacidadeProdutoGrupo, Cidade, CompraMateriaPrima,
    ConsolidadoRodadaGrupo, Decisao, Distribuicao, EstoqueMateriaPrima,
    Evento, GameConfig, Grupo, Jogo, MateriaPrima, Producao, Produto,
    ResultadoFinanceiro, Rodada, User,
)


class PrimeiraTurmaTest(TestCase):
    def login(self, usuario):
        self.client.logout()
        self.assertTrue(self.client.login(username=usuario.email_usuario, password="SenhaTurma42"))

    def painel(self, dados):
        resposta = self.client.post(reverse("painel_grupo"), dados, follow=True)
        self.assertEqual(resposta.status_code, 200)
        return resposta

    def test_professor_ceo_membro_ate_classificacao_final(self):
        call_command("seed_dados_base", stdout=StringIO())
        prof = User.objects.create_user("prof@turma.edu", "Professor", "SenhaTurma42", tipo_usuario="gamemaster")
        self.login(prof)
        # Configuração pública do professor: pesos usados de verdade no fechamento.
        dados = {
            "capital_inicial": "1000000", "estoque_inicial": 0,
            "maquinas_iniciais": 40, "maquinas_iniciais_a": 15,
            "maquinas_iniciais_b": 15, "maquinas_iniciais_c": 10,
            "trabalhadores_iniciais": 80, "numero_rodadas": 5,
            "produtos_habilitados": "A,B,C", "modulo_producao": "on",
            "modulo_distribuicao": "on", "modulo_financeiro": "on",
            "regra_eventos": "{}", "peso_eo": "1", "peso_df": "0",
            "peso_ee": "0", "peso_sd": "0", "peso_ds": "0",
        }
        resposta = self.client.post(reverse("game_config"), dados)
        self.assertEqual(resposta.status_code, 302)
        jogo = Jogo.objects.get(nome="Jogo Principal")
        equipes = []
        for nome in ("Vega", "Rigel", "Sirius", "Altair", "Deneb"):
            cadastro = {"nome": nome, "jogo": jogo.pk, "form-TOTAL_FORMS": 3,
                        "form-INITIAL_FORMS": 0}
            for i in range(3):
                cadastro.update({f"form-{i}-nome": f"{nome} {i}",
                                 f"form-{i}-email": f"{nome.lower()}{i}@turma.edu",
                                 f"form-{i}-senha": "SenhaTurma42"})
            cadastro["form-0-lider"] = "on"
            self.assertEqual(self.client.post(reverse("criar_grupo"), cadastro).status_code, 302)
            grupo = Grupo.objects.get(nome=nome)
            self.assertEqual(grupo.capital, Decimal("1000000"))
            self.assertEqual(grupo.maquinas, 40)
            equipes.append(grupo)

        # Outro jogo permanece intacto durante o fechamento da turma.
        outro = Jogo.objects.create(nome="Outra turma", config=GameConfig.objects.create())
        rival = Grupo.objects.create(nome="Fora da turma", jogo=outro, capital=999)
        produto = Produto.objects.get(codigo="A")
        estabilidade = Evento.objects.get(nome="Estabilidade econômica")
        # 7.1, tabela de fornecedores por materia-prima
        fornecedores = {"MP1": ("Fortaleza", 120), "MP2": ("Recife", 40),
                        "MP3": ("Aracaju", 60), "MP4": ("João Pessoa", 80)}

        with patch("app.services.eventos.random.choices", return_value=[estabilidade]):
            for numero in (1, 2, 3, 4, 5):
                self.login(prof)
                resposta = self.client.post(reverse("abrir_rodada"), {
                    "jogo": jogo.pk, "numero": numero,
                    "fim": timezone.now() + timedelta(hours=1),
                })
                self.assertEqual(resposta.status_code, 302)
                rodada = Rodada.objects.get(jogo=jogo, numero=numero)
                for grupo in equipes:
                    membro = grupo.membros.exclude(pk=grupo.lider_id).first()
                    self.login(membro)
                    self.painel({"enviar_decisao": "1", "descricao": "Tentativa do membro", "quantidade": 0})
                    self.assertFalse(Decisao.objects.filter(grupo=grupo, rodada=numero).exists())
                    self.login(grupo.lider)
                    if numero == 1:
                        for codigo, (cidade, kg) in fornecedores.items():
                            self.painel({"enviar_compra_mp": "1",
                                         "materia_prima": MateriaPrima.objects.get(codigo=codigo).pk,
                                         "cidade_fornecedora": Cidade.objects.get(nome=cidade).pk,
                                         "quantidade_kg": kg})
                        compras = CompraMateriaPrima.objects.filter(grupo=grupo)
                        self.assertEqual(compras.count(), 4)
                        self.assertEqual(set(compras.values_list("rodada_recebimento", flat=True)), {2})
                        self.assertFalse(compras.filter(recebida=True).exists())
                        self.assertFalse(EstoqueMateriaPrima.objects.filter(grupo=grupo, quantidade_kg__gt=0).exists())
                        # 11.3.b: a ordem e aceita; quem produz e o fechamento.
                        # Na rodada 1 nao ha MP -- ela chega na seguinte (7.3) --
                        # entao a ordem fica registrada e produz zero (13.11).
                        self.painel({"enviar_producao": "1", "produto": produto.pk, "quantidade_planejada": 1})
                        ordem = Producao.objects.get(grupo=grupo, rodada=1)
                        self.assertEqual(ordem.quantidade_planejada, 1)
                        self.assertEqual(ordem.quantidade_produzida, 0)
                    elif numero == 2:
                        self.painel({"enviar_producao": "1", "produto": produto.pk, "quantidade_planejada": 1})
                        # Agora ha MP: a ordem so vira produto no fechamento.
                        self.assertEqual(Producao.objects.get(grupo=grupo, rodada=2).quantidade_planejada, 1)
                        self.assertEqual(Producao.objects.get(grupo=grupo, rodada=2).quantidade_produzida, 0)
                        self.assertFalse(CompraMateriaPrima.objects.filter(grupo=grupo, recebida=False).exists())
                        self.painel({"enviar_envio": "1", "produto": produto.pk,
                                     # Natal e a fabrica (9), nao praca de venda
                                     "cidade": Cidade.objects.get(nome="Recife").pk,
                                     "quantidade": 1, "preco_unitario": "5000"})
                        self.assertEqual(Distribuicao.objects.get(grupo=grupo, rodada=2).quantidade_vendida, 0)

                    capacidades = CapacidadeProdutoGrupo.objects.filter(grupo=grupo)
                    self.assertEqual(sum(c.maquinas for c in capacidades), 40)
                    self.assertEqual(sum(c.operadores for c in capacidades), 80)
                    self.painel({"enviar_decisao": "1"})
                    decisao = Decisao.objects.get(grupo=grupo, rodada=numero)
                    criada_em = decisao.data_criacao
                    # 11.2: submeter e o ato que fecha a rodada. A segunda
                    # tentativa e recusada -- antes o teste provava isso pelo
                    # texto digitado, que saiu da tela em 25/09/2026 porque
                    # regra nenhuma o lia.
                    self.painel({"enviar_decisao": "1"})
                    decisao.refresh_from_db()
                    self.assertEqual(Decisao.objects.filter(grupo=grupo, rodada=numero).count(), 1)
                    self.assertEqual(decisao.data_criacao, criada_em)
                    auditoria = AuditoriaSubmissaoRodada.objects.get(grupo=grupo, rodada=numero)
                    self.assertEqual(auditoria.usuario_id, grupo.lider_id)
                    self.assertIsNotNone(auditoria.data_registro)
                    relatorio = self.client.get(reverse("relatorios"))
                    self.assertNotIn(numero, {r.rodada for r in relatorio.context["resultados"]})

                self.login(prof)
                gerenciamento = self.client.get(reverse("gerenciamento_jogo"))
                self.assertEqual(gerenciamento.status_code, 200)
                self.assertContains(gerenciamento, "Vega")
                # Avanço de relógio: o comando real deve processar somente vencidas.
                Rodada.objects.filter(pk=rodada.pk).update(fim=timezone.now() - timedelta(seconds=1))
                call_command("fechar_rodadas", stdout=StringIO())
                rodada.refresh_from_db()
                self.assertTrue(rodada.fechada)
                for grupo in equipes:
                    resumo = ConsolidadoRodadaGrupo.objects.get(grupo=grupo, rodada=numero)
                    self.assertEqual(resumo.penalidade_sem_submissao, 0)
                    self.assertEqual(resumo.score_multicriterio, resumo.eo_percent)
                    if numero == 2:
                        self.assertEqual(resumo.total_vendido, 1)
                        self.assertEqual(resumo.receita_vendas, Decimal("5000"))
                    self.login(grupo.lider)
                    self.assertEqual(self.client.get(reverse("encerramento_rodada")).context["rodada"].numero, numero)
                    self.assertEqual(self.client.get(reverse("ranking")).context["rodada_referencia"], numero)

        antes = list(ResultadoFinanceiro.objects.order_by("pk").values())
        call_command("fechar_rodadas", stdout=StringIO())
        self.assertEqual(list(ResultadoFinanceiro.objects.order_by("pk").values()), antes)
        self.assertEqual(ConsolidadoRodadaGrupo.objects.count(), 25)
        rival.refresh_from_db()
        self.assertEqual(rival.capital, 999)
        for grupo in equipes:
            self.login(grupo.membros.exclude(pk=grupo.lider_id).first())
            final = self.client.get(reverse("classificacao_final"))
            self.assertEqual({g["grupo"].pk for g in final.context["grupos"]}, {g.pk for g in equipes})
            for nome in ("relatorios", "relatorios_comparativos", "export_resultados_pdf", "export_resultados_excel"):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 200)
