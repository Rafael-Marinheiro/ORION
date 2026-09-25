# -*- coding: utf-8 -*-
"""O mapa poe cada praca do 9.1 no lugar real dela.

O 9 fixa a fabrica em Natal-RN e lista dez cidades de venda. A lista de
satisfacao por praca ja existia no painel; o mapa mostra ONDE, e a barra de
cada cidade sobe do ponto geografico. Nenhuma regra usa estas coordenadas:
as distancias continuam vindo de `Cidade.distancia_km`, como o 9.1 manda.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.geografia import (
    CIDADE_SEDE,
    COORDENADAS_PRACAS,
    montar_mapa,
    ponto_da_praca,
    projetar,
)
from app.models import Cidade, Distribuicao, Grupo, Produto, Rodada, User


class _CidadeFalsa:
    def __init__(self, nome):
        self.nome = nome


def _linha(nome, percentual):
    return {
        "cidade": _CidadeFalsa(nome),
        "percentual": Decimal(str(percentual)),
        "vendidas": 10,
        "demanda": 100,
    }


class ProjecaoTest(TestCase):
    def test_as_dez_pracas_do_9_1_mais_a_sede_tem_coordenada(self):
        self.assertIn(CIDADE_SEDE, COORDENADAS_PRACAS)
        self.assertEqual(len(COORDENADAS_PRACAS), 11)

    def test_o_norte_fica_acima_e_o_sul_abaixo(self):
        _, y_belem = projetar(*COORDENADAS_PRACAS["Belém"])
        _, y_sao_paulo = projetar(*COORDENADAS_PRACAS["São Paulo"])
        _, y_porto_alegre = projetar(*COORDENADAS_PRACAS["Porto Alegre"])

        self.assertLess(y_belem, y_sao_paulo)
        self.assertLess(y_sao_paulo, y_porto_alegre)

    def test_o_litoral_leste_fica_a_direita_do_interior(self):
        x_recife, _ = projetar(*COORDENADAS_PRACAS["Recife"])
        x_goiania, _ = projetar(*COORDENADAS_PRACAS["Goiânia"])

        self.assertGreater(x_recife, x_goiania)

    def test_cidade_fora_do_9_1_nao_tem_ponto(self):
        self.assertIsNone(ponto_da_praca("Curitiba"))


class MontagemDoMapaTest(TestCase):
    def test_a_altura_da_barra_acompanha_o_percentual(self):
        barras, _ = montar_mapa([_linha("Recife", 100), _linha("Belém", 0)])

        alturas = {barra["nome"]: barra["altura"] for barra in barras}
        self.assertEqual(alturas["Recife"], 72)
        self.assertEqual(alturas["Belém"], 0)

    def test_a_cidade_sem_coordenada_sai_da_planta_mas_nao_some(self):
        barras, fora = montar_mapa([_linha("Recife", 50), _linha("Curitiba", 80)])

        self.assertEqual([barra["nome"] for barra in barras], ["Recife"])
        self.assertEqual(fora, ["Curitiba"])

    def test_os_rotulos_do_nordeste_nao_se_sobrepoem(self):
        """Cinco capitais em cinco graus de latitude: girado o mapa, elas
        ainda ficam a poucos pixels uma da outra."""
        barras, _ = montar_mapa(
            [
                _linha(nome, 50)
                for nome in ("Natal", "João Pessoa", "Recife", "Maceió", "Aracaju")
            ]
        )

        alturas = sorted(barra["rotulo_y"] for barra in barras)
        for anterior, seguinte in zip(alturas, alturas[1:]):
            self.assertGreaterEqual(seguinte - anterior, 12)

    def test_as_barras_saem_ordenadas_de_tras_para_a_frente(self):
        barras, _ = montar_mapa(
            [_linha("Porto Alegre", 40), _linha("Belém", 40), _linha("Goiânia", 40)]
        )

        self.assertEqual(
            [barra["nome"] for barra in barras], ["Belém", "Goiânia", "Porto Alegre"]
        )


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class MapaNoPainelTest(TestCase):
    def setUp(self):
        self.ceo = User.objects.create_user(
            email_usuario="ceo-mapa@example.com", nome_usuario="CEO",
            password="pass", tipo_usuario="lider_grupo",
        )
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("1000"))
        self.grupo.membros.add(self.ceo)
        produto = Produto.objects.create(codigo="A", nome="Produto A", tempo_producao_min=2)
        cidade = Cidade.objects.create(nome="Recife", distancia_km=290, demanda=4000)
        # rodada aberta: e dela que o painel tira o mapa sem filtro
        Rodada.objects.create(numero=1, fim=timezone.now() + timedelta(hours=1))
        Distribuicao.objects.create(
            grupo=self.grupo, produto=produto, cidade=cidade, rodada=1,
            quantidade=100, quantidade_vendida=80, preco_unitario=Decimal("10"),
            custo_transporte=Decimal("0"),
        )
        self.client.login(username="ceo-mapa@example.com", password="pass")

    def test_o_painel_desenha_a_praca_atendida(self):
        resposta = self.client.get(reverse("painel_grupo"))

        self.assertEqual(
            [barra["nome"] for barra in resposta.context["mapa_barras"]], ["Recife"]
        )
        self.assertContains(resposta, 'class="o-mapa"')
        # 80 de 4.000: arredondar para inteiro escreveria "2%" -- aqui a
        # casa decimal existe justamente porque abaixo de 10% ela muda o
        # que o aluno le.
        self.assertContains(resposta, "Recife 2,0%")

    def test_as_coordenadas_do_svg_nao_saem_com_virgula(self):
        """L10N do Django formata float como "303,0" -- coordenada invalida
        em SVG, e o mapa inteiro sumia."""
        corpo = self.client.get(reverse("painel_grupo")).content.decode()

        self.assertNotRegex(corpo, r'c[xy]="\d+,\d')
        self.assertNotRegex(corpo, r'<rect class="o-mapa__[a-z]+" x="\d+,\d')
