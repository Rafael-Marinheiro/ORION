# -*- coding: utf-8 -*-
"""Surto de gripe: o primeiro evento em que a equipe responde.

Ate aqui todo evento era passivo -- sorteia, aplica igual para todos,
calcula. Este faz uma oferta uniforme e o resultado depende da resposta de
cada equipe.

PENDENTE DE RATIFICACAO. O 8.2 diz "o evento sorteado afeta todos os grupos
de maneira igual" e o 8.3 nao lista forca de trabalho nem caixa entre as
variaveis afetadas. A leitura adotada e que a OFERTA e uniforme e a
consequencia e da gestao; cabe ao autor da especificacao confirmar.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import (
    CEOGrupoRodada,
    CapacidadeProdutoGrupo,
    DecisaoEventoGrupo,
    Evento,
    EventoRodada,
    GameConfig,
    Grupo,
    Jogo,
    Produto,
    Rodada,
    User,
)
from app.services.eventos import (
    custo_da_oferta,
    evento_de_decisao,
    fracao_de_operadores,
    registrar_decisao,
    resolver_decisao,
)


def _surto(**extra):
    campos = {
        "tipo": "greve",
        "modo_aplicacao": "decisao",
        "efeito_estado": "afastamento_equipe",
        "impacto_percentual_minimo": 20,
        "impacto_percentual": 20,
        "custo_unitario_decisao": Decimal("180.00"),
        "probabilidade": 9,
        "extensao": True,
    }
    campos.update(extra)
    return Evento.objects.create(nome="Surto de gripe", **campos)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class OfertaDoSurtoTest(TestCase):
    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=4)
        )
        self.grupo = Grupo.objects.create(
            nome="Equipe Vega", jogo=self.jogo,
            capital=Decimal("1000000"), trabalhadores=80,
        )
        self.rodada = Rodada.objects.create(
            jogo=self.jogo, numero=1, fim=timezone.now() + timedelta(hours=2)
        )
        self.evento = _surto()
        EventoRodada.objects.create(
            rodada=1, jogo=self.jogo, evento=self.evento, manual=True
        )

    def test_a_oferta_custa_por_trabalhador(self):
        """Quem investiu em pessoal paga mais: nao e taxa fixa."""
        self.assertEqual(
            custo_da_oferta(self.evento, self.grupo), Decimal("14400.00")
        )

    def test_a_oferta_aparece_como_evento_de_decisao_da_rodada(self):
        self.assertEqual(evento_de_decisao(1, self.jogo.id), self.evento)

    def test_quem_aceita_paga_e_nao_perde_ninguem(self):
        registrar_decisao(self.grupo, 1, self.evento, True)

        custo, afetados = resolver_decisao(self.grupo, 1, self.evento)

        self.assertEqual(custo, Decimal("14400.00"))
        self.assertEqual(afetados, 0)
        self.assertEqual(fracao_de_operadores(self.grupo, 1), 1.0)

    def test_quem_recusa_nao_paga_e_perde_parte_da_equipe(self):
        registrar_decisao(self.grupo, 1, self.evento, False)

        custo, afetados = resolver_decisao(self.grupo, 1, self.evento)

        self.assertEqual(custo, Decimal("0"))
        self.assertEqual(afetados, 20)
        self.assertAlmostEqual(fracao_de_operadores(self.grupo, 1), 0.8)

    def test_quem_nao_responde_e_tratado_como_recusa(self):
        """11: decisao ausente nao vira isencao -- nada foi pago."""
        custo, afetados = resolver_decisao(self.grupo, 1, self.evento)

        self.assertEqual(custo, Decimal("0"))
        self.assertEqual(afetados, 20)
        self.assertTrue(
            DecisaoEventoGrupo.objects.filter(
                grupo=self.grupo, rodada=1, evento=self.evento
            ).exists()
        )

    def test_o_afastamento_e_sorteado_uma_vez_so(self):
        """O numero nao pode mudar a cada consulta do relatorio."""
        evento = Evento.objects.create(
            nome="Surto largo", tipo="greve", modo_aplicacao="decisao",
            efeito_estado="afastamento_equipe", impacto_percentual_minimo=10,
            impacto_percentual=60, custo_unitario_decisao=Decimal("10"),
            probabilidade=0, extensao=True,
        )
        EventoRodada.objects.create(
            rodada=1, jogo=self.jogo, evento=evento, manual=True
        )

        primeiro = resolver_decisao(self.grupo, 1, evento)
        for _ in range(8):
            self.assertEqual(resolver_decisao(self.grupo, 1, evento), primeiro)

    def test_a_faixa_respeita_o_piso_e_o_teto(self):
        evento = Evento.objects.create(
            nome="Surto faixa", tipo="greve", modo_aplicacao="decisao",
            efeito_estado="afastamento_equipe", impacto_percentual_minimo=15,
            impacto_percentual=35, custo_unitario_decisao=Decimal("10"),
            probabilidade=0, extensao=True,
        )
        for indice in range(30):
            grupo = Grupo.objects.create(
                nome=f"Equipe {indice}", jogo=self.jogo, trabalhadores=80
            )
            _, afetados = resolver_decisao(grupo, 1, evento)
            self.assertGreaterEqual(afetados, 15)
            self.assertLessEqual(afetados, 35)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class AfastamentoDerrubaACapacidadeTest(TestCase):
    """RN-06: "cada maquina exige 2 trabalhadores. Maquinas sem operadores
    nao produzem"."""

    def test_metade_dos_operadores_derruba_o_teto_da_linha(self):
        jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=4)
        )
        grupo = Grupo.objects.create(nome="Equipe Vega", jogo=jogo)
        produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=10
        )
        linha = CapacidadeProdutoGrupo.objects.create(
            grupo=grupo, produto=produto, maquinas=15, operadores=30,
            minutos_por_maquina=400,
        )

        cheio = linha.capacidade_com_operadores(1.0)
        pela_metade = linha.capacidade_com_operadores(0.5)

        self.assertEqual(cheio, 600)
        self.assertEqual(pela_metade, 280)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class PainelDaOfertaTest(TestCase):
    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=4)
        )
        self.grupo = Grupo.objects.create(
            nome="Equipe Vega", jogo=self.jogo,
            capital=Decimal("1000000"), trabalhadores=80,
        )
        self.ceo = User.objects.create_user(
            email_usuario="ceo-surto@example.com", nome_usuario="CEO",
            password="senha12345", tipo_usuario="lider_grupo",
        )
        self.grupo.membros.add(self.ceo)
        self.grupo.lider = self.ceo
        self.grupo.save()
        Rodada.objects.create(
            jogo=self.jogo, numero=1, fim=timezone.now() + timedelta(hours=2)
        )
        CEOGrupoRodada.objects.create(grupo=self.grupo, rodada=1, usuario=self.ceo)
        self.evento = _surto()
        EventoRodada.objects.create(
            rodada=1, jogo=self.jogo, evento=self.evento, manual=True
        )
        self.client.force_login(self.ceo)

    def test_o_painel_mostra_a_oferta_com_o_preco(self):
        resposta = self.client.get(reverse("painel_grupo"))

        self.assertContains(resposta, "Surto de gripe")
        self.assertContains(resposta, "14.400,00")
        self.assertContains(resposta, "Contratar a imunização")

    def test_o_painel_nao_diz_o_tamanho_do_risco(self):
        """O aluno sabe que ha risco, nao quanto. Medir o risco e parte do
        que se avalia."""
        corpo = self.client.get(reverse("painel_grupo")).content.decode()

        self.assertNotIn("20%", corpo.split("Surto de gripe")[1][:1500])

    def test_o_ceo_responde_pela_tela(self):
        self.client.post(
            reverse("painel_grupo"), {"responder_oferta": "aceitar"}
        )

        decisao = DecisaoEventoGrupo.objects.get(grupo=self.grupo, rodada=1)
        self.assertTrue(decisao.aceitou)

    def test_a_resposta_pode_ser_trocada_antes_da_submissao(self):
        self.client.post(reverse("painel_grupo"), {"responder_oferta": "aceitar"})
        self.client.post(reverse("painel_grupo"), {"responder_oferta": "recusar"})

        self.assertEqual(
            DecisaoEventoGrupo.objects.filter(grupo=self.grupo, rodada=1).count(), 1
        )
        self.assertFalse(
            DecisaoEventoGrupo.objects.get(grupo=self.grupo, rodada=1).aceitou
        )
