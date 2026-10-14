# -*- coding: utf-8 -*-
"""A Ajuda publica os dados de referencia do 7.1, 9.1 e 9.2.

`distancia_km` e `demanda_maxima` nao apareciam em template nenhum do
sistema: o aluno decidia para onde enviar sem saber a distancia, que
define o frete, nem quanto a praca absorve, que limita a venda. O mesmo
valia para os fornecedores por materia-prima do 7.1.

Isto nao contraria a regra de nao antecipar ao aluno o efeito das escolhas
dele: sao parametros publicos do mercado, iguais para todos e necessarios
ANTES da decisao -- como as caracteristicas dos produtos, que ja estavam
aqui pelo mesmo motivo.
"""

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from app.models import Cidade, MateriaPrima


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class ReferenciaNaAjudaTest(TestCase):
    def setUp(self):
        call_command("seed_dados_base")

    def test_as_dez_pracas_aparecem_com_distancia(self):
        resposta = self.client.get(reverse("ajuda"))

        corpo = resposta.content.decode()
        # L10N pt-BR separa o milhar: "4.034 km"
        for nome, distancia in [
            ("João Pessoa", "181"),
            ("Recife", "290"),
            ("Fortaleza", "527"),
            ("Porto Alegre", "4.034"),
        ]:
            self.assertIn(nome, corpo, nome)
            self.assertIn(f"{distancia} km", corpo, nome)

    def test_a_demanda_maxima_da_praca_aparece(self):
        resposta = self.client.get(reverse("ajuda"))

        # 9.1: Sao Paulo tem o maior teto, 27.000 por produto
        self.assertContains(resposta, "27.000 un")

    def test_os_fornecedores_do_7_1_aparecem_por_materia_prima(self):
        resposta = self.client.get(reverse("ajuda"))

        contexto = {mp.codigo: mp for mp in resposta.context["materias_primas"]}
        self.assertEqual(
            {c.nome for c in contexto["MP1"].fornecedores.all()},
            {"Fortaleza", "Maceió"},
        )
        self.assertEqual(
            {c.nome for c in contexto["MP4"].fornecedores.all()},
            {"São Paulo", "João Pessoa", "Goiânia"},
        )

    def test_os_parametros_de_frete_aparecem(self):
        """9.2 e 7.2: o aluno nao tinha como calcular o frete antes."""
        resposta = self.client.get(reverse("ajuda"))

        self.assertContains(resposta, "R$ 1,50 por km")
        self.assertContains(resposta, "R$ 5,00 por km")
        self.assertContains(resposta, "12.000 kg")

    def test_a_capacidade_da_linha_aparece(self):
        resposta = self.client.get(reverse("ajuda"))

        self.assertContains(resposta, "400 minutos")
        self.assertContains(resposta, "2 operadores")

    def test_o_sumario_leva_a_cada_secao(self):
        resposta = self.client.get(reverse("ajuda"))

        corpo = resposta.content.decode()
        for ancora in [
            "primeiros-passos", "produtos", "materias-primas",
            "pracas", "logistica", "classificacao", "faq",
        ]:
            self.assertIn(f'href="#{ancora}"', corpo, ancora)
            self.assertIn(f'id="{ancora}"', corpo, ancora)

    def test_a_ajuda_continua_publica(self):
        """Visitante sem conta precisa conseguir ler as regras."""
        resposta = self.client.get(reverse("ajuda"))

        self.assertEqual(resposta.status_code, 200)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class FornecedorRestritoTest(TestCase):
    """7.1: "a escolha do fornecedor sera realizada no momento da compra,
    influenciando diretamente o custo logistico".

    O formulario aceitava QUALQUER praca. A compra mais barata virava
    trazer as quatro MPs da praca mais proxima -- Joao Pessoa, a 181 km --,
    e o 7.1 deixava de existir: ninguem compraria MP1 em Fortaleza (527 km)
    nem MP3 em Aracaju (782 km).
    """

    def setUp(self):
        call_command("seed_dados_base")
        self.mp1 = MateriaPrima.objects.get(codigo="MP1")

    def _form(self, cidade_nome):
        from app.forms import CompraMateriaPrimaForm

        return CompraMateriaPrimaForm({
            "materia_prima": self.mp1.pk,
            "cidade_fornecedora": Cidade.objects.get(nome=cidade_nome).pk,
            "quantidade_kg": "100",
        })

    def test_fornecedor_do_documento_e_aceito(self):
        self.assertTrue(self._form("Fortaleza").is_valid())
        self.assertTrue(self._form("Maceió").is_valid())

    def test_praca_que_nao_fornece_aquela_mp_e_recusada(self):
        form = self._form("João Pessoa")

        self.assertFalse(form.is_valid())
        self.assertIn("cidade_fornecedora", form.errors)

    def test_o_erro_diz_onde_comprar(self):
        """Recusar sem dizer onde comprar deixa o aluno travado."""
        form = self._form("São Paulo")
        form.is_valid()

        erro = " ".join(form.errors["cidade_fornecedora"])
        self.assertIn("Fortaleza", erro)
        self.assertIn("Maceió", erro)

    def test_materia_prima_sem_fornecedor_cadastrado_nao_trava_a_compra(self):
        """Base antiga, sem o vinculo do 7.1, nao pode bloquear a turma."""
        self.mp1.fornecedores.clear()

        self.assertTrue(self._form("São Paulo").is_valid())
