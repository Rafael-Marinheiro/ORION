# -*- coding: utf-8 -*-
"""O professor pode determinar o evento da rodada.

O 8.2 sorteia um evento por rodada pelos pesos do 8.4, e continua sendo o
que acontece quando o professor nao toca em nada. A partir de 25/09/2026 ele
pode dirigir a aula: escolher um evento do catalogo ou descrever um novo em
termos do que faz com uma metrica -- demanda, custo de producao ou custo de
transporte -- para todas as pracas ou so para algumas.

A opcao "deixar tambem um evento sorteado acontecer" faz a rodada ter dois.
Nao e invencao: a RN-10 do 5 diz que "a cada rodada, o sistema pode ativar
ate 2 eventos aleatorios simultaneos" e que "a ativacao e definida pelo
moderador ou aleatoriamente, conforme configuracao". A regra estava
registrada como AUSENTE no guia desde 18/09/2026. A decisao B4 escolheu o
8.2 para o SORTEIO -- que segue sorteando um so.
"""

from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import (
    CapacidadeProdutoGrupo,
    Cidade,
    ComposicaoProduto,
    DemandaCidadeProduto,
    Distribuicao,
    EstoqueMateriaPrima,
    Evento,
    EventoRodada,
    GameConfig,
    Grupo,
    Jogo,
    MateriaPrima,
    Producao,
    Produto,
    Rodada,
    User,
)
from app.services.eventos import (
    efeito_absoluto,
    eventos_da_rodada,
    fator_percentual,
    sortear_evento,
)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class AberturaComEventoTest(TestCase):
    def setUp(self):
        self.professor = User.objects.create_user(
            email_usuario="prof-evento@example.com", nome_usuario="Professora",
            password="pass", tipo_usuario="gamemaster",
        )
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=4)
        )
        Grupo.objects.create(nome="Equipe Vega", jogo=self.jogo)
        self.catalogo = Evento.objects.create(
            nome="Greve de caminhoneiros", tipo="custo_transporte",
            modo_aplicacao="percentual", impacto_percentual=30, probabilidade=20,
        )
        self.recife = Cidade.objects.create(
            nome="Recife", distancia_km=290, demanda=4000
        )
        self.sp = Cidade.objects.create(
            nome="São Paulo", distancia_km=2896, demanda=27000
        )
        self.client.force_login(self.professor)

    def _abrir(self, **extra):
        dados = {
            "jogo": self.jogo.id,
            "numero": 1,
            "fim": (timezone.now() + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M"),
        }
        dados.update(extra)
        return self.client.post(reverse("abrir_rodada"), dados)

    def test_sem_marcar_nada_a_rodada_segue_o_sorteio(self):
        self._abrir()

        rodada = Rodada.objects.get(jogo=self.jogo, numero=1)
        self.assertTrue(rodada.sorteio_evento)
        self.assertFalse(EventoRodada.objects.filter(rodada=1, jogo=self.jogo).exists())

    def test_evento_do_catalogo_entra_na_rodada_e_desliga_o_sorteio(self):
        self._abrir(
            adicionar_evento="on",
            origem_evento="catalogo",
            evento_existente=self.catalogo.id,
        )

        rodada = Rodada.objects.get(jogo=self.jogo, numero=1)
        registro = EventoRodada.objects.get(rodada=1, jogo=self.jogo)
        self.assertEqual(registro.evento, self.catalogo)
        self.assertTrue(registro.manual)
        self.assertFalse(rodada.sorteio_evento)
        self.assertIsNone(sortear_evento(1, jogo_id=self.jogo.id))

    def test_evento_manual_pode_conviver_com_o_sorteado(self):
        """RN-10: "ate 2 eventos aleatorios simultaneos" por rodada."""
        Evento.objects.create(
            nome="Superoferta agrícola", tipo="custo_producao",
            modo_aplicacao="percentual", impacto_percentual=-10, probabilidade=80,
        )
        self._abrir(
            adicionar_evento="on",
            origem_evento="catalogo",
            evento_existente=self.catalogo.id,
            evento_com_sorteio="on",
        )

        rodada = Rodada.objects.get(jogo=self.jogo, numero=1)
        self.assertTrue(rodada.sorteio_evento)

        sorteado = sortear_evento(1, jogo_id=self.jogo.id)

        self.assertIsNotNone(sorteado)
        self.assertNotEqual(sorteado, self.catalogo)
        self.assertEqual(
            EventoRodada.objects.filter(rodada=1, jogo=self.jogo).count(), 2
        )

    def test_o_sorteio_nao_repete_o_evento_que_o_professor_escolheu(self):
        """Com um catalogo de um evento so, nao ha segundo evento possivel --
        e repetir o mesmo seria anunciar duas vezes a mesma noticia."""
        self._abrir(
            adicionar_evento="on",
            origem_evento="catalogo",
            evento_existente=self.catalogo.id,
            evento_com_sorteio="on",
        )

        self.assertIsNone(sortear_evento(1, jogo_id=self.jogo.id))
        self.assertEqual(
            EventoRodada.objects.filter(rodada=1, jogo=self.jogo).count(), 1
        )

    def test_evento_novo_guarda_o_sinal_do_efeito_escolhido(self):
        """O professor escolhe em palavras; o sinal e problema do sistema."""
        self._abrir(
            adicionar_evento="on",
            origem_evento="novo",
            evento_nome="Feira regional",
            evento_frase="A feira da cidade aqueceu as vendas.",
            evento_tipo="demanda",
            evento_sentido="beneficio",
            evento_medida="percentual",
            evento_valor="20",
        )

        evento = Evento.objects.get(manual=True)
        self.assertEqual(evento.impacto_percentual, 20)
        self.assertEqual(evento.tipo, "demanda")
        self.assertEqual(evento.jogo, self.jogo)
        self.assertEqual(evento.probabilidade, 0)
        self.assertEqual(evento.frase_indicativa, "A feira da cidade aqueceu as vendas.")

    def test_custo_que_ajuda_a_equipe_entra_negativo(self):
        self._abrir(
            adicionar_evento="on",
            origem_evento="novo",
            evento_nome="Diesel mais barato",
            evento_tipo="custo_transporte",
            evento_sentido="beneficio",
            evento_medida="percentual",
            evento_valor="15",
        )

        self.assertEqual(Evento.objects.get(manual=True).impacto_percentual, -15)

    def test_evento_em_valor_absoluto_e_restrito_as_pracas_marcadas(self):
        self._abrir(
            adicionar_evento="on",
            origem_evento="novo",
            evento_nome="Enchente no Recife",
            evento_tipo="demanda",
            evento_sentido="prejuizo",
            evento_medida="absoluto",
            evento_valor="500",
            evento_cidades=[self.recife.id],
        )

        evento = Evento.objects.get(manual=True)
        self.assertEqual(evento.modo_aplicacao, "absoluto")
        self.assertEqual(evento.valor_absoluto, Decimal("-500"))
        self.assertEqual([c.nome for c in evento.cidades.all()], ["Recife"])

    def test_evento_sem_praca_marcada_vale_para_todas(self):
        self._abrir(
            adicionar_evento="on",
            origem_evento="novo",
            evento_nome="Feira nacional",
            evento_tipo="demanda",
            evento_sentido="beneficio",
            evento_medida="percentual",
            evento_valor="10",
        )

        evento = Evento.objects.get(manual=True)
        self.assertEqual(evento.cidades.count(), 0)
        self.assertEqual(fator_percentual([evento], "demanda", self.sp.id), Decimal("1.1"))

    def test_o_evento_do_professor_nao_entra_no_sorteio_de_outras_rodadas(self):
        self._abrir(
            adicionar_evento="on",
            origem_evento="novo",
            evento_nome="Feira regional",
            evento_tipo="demanda",
            evento_sentido="beneficio",
            evento_medida="percentual",
            evento_valor="20",
        )

        manual = Evento.objects.get(manual=True)
        sorteados = {sortear_evento(n, jogo_id=self.jogo.id) for n in range(2, 12)}

        self.assertNotIn(manual, sorteados)

    def test_o_formulario_recusa_evento_sem_intensidade(self):
        resposta = self._abrir(
            adicionar_evento="on",
            origem_evento="novo",
            evento_nome="Sem número",
            evento_tipo="demanda",
            evento_sentido="prejuizo",
            evento_medida="percentual",
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("evento_valor", resposta.context["form"].errors)
        self.assertFalse(Rodada.objects.filter(jogo=self.jogo, numero=1).exists())

    def test_o_formulario_recusa_catalogo_sem_escolha(self):
        resposta = self._abrir(adicionar_evento="on", origem_evento="catalogo")

        self.assertIn("evento_existente", resposta.context["form"].errors)


class EfeitoDeVariosEventosTest(TestCase):
    """Dois eventos na mesma rodada compoem; nao se substituem."""

    def setUp(self):
        self.recife = Cidade.objects.create(
            nome="Recife", distancia_km=290, demanda=4000
        )
        self.sp = Cidade.objects.create(
            nome="São Paulo", distancia_km=2896, demanda=27000
        )

    def _evento(self, **campos):
        padrao = {
            "nome": "Evento", "tipo": "demanda", "modo_aplicacao": "percentual",
            "impacto_percentual": 0, "probabilidade": 0,
        }
        padrao.update(campos)
        return Evento.objects.create(**padrao)

    def test_dois_percentuais_do_mesmo_tipo_se_multiplicam(self):
        um = self._evento(tipo="custo_producao", impacto_percentual=10)
        outro = self._evento(tipo="custo_producao", impacto_percentual=20)

        self.assertEqual(
            fator_percentual([um, outro], "custo_producao"), Decimal("1.32")
        )

    def test_evento_de_outro_tipo_nao_interfere(self):
        demanda = self._evento(tipo="demanda", impacto_percentual=50)

        self.assertEqual(fator_percentual([demanda], "custo_producao"), Decimal("1"))

    def test_o_efeito_local_nao_alcanca_a_outra_praca(self):
        local = self._evento(tipo="demanda", impacto_percentual=-40)
        local.cidades.set([self.recife])

        self.assertEqual(fator_percentual([local], "demanda", self.recife.id), Decimal("0.6"))
        self.assertEqual(fator_percentual([local], "demanda", self.sp.id), Decimal("1"))

    def test_valor_absoluto_soma_em_vez_de_multiplicar(self):
        queda = self._evento(
            tipo="demanda", modo_aplicacao="absoluto", valor_absoluto=Decimal("-500")
        )

        self.assertEqual(efeito_absoluto([queda], "demanda"), Decimal("-500"))
        self.assertEqual(fator_percentual([queda], "demanda"), Decimal("1"))


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class FechamentoComEventoManualTest(TestCase):
    """O fechamento aplica o evento do professor como aplica o sorteado."""

    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=4)
        )
        self.grupo = Grupo.objects.create(
            nome="Equipe Vega", jogo=self.jogo, capital=Decimal("1000000")
        )
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=1
        )
        mp = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("1")
        )
        ComposicaoProduto.objects.create(
            produto=self.produto, materia_prima=mp,
            quantidade_por_unidade=Decimal("1"),
        )
        EstoqueMateriaPrima.objects.create(
            grupo=self.grupo, materia_prima=mp, quantidade_kg=Decimal("5000")
        )
        CapacidadeProdutoGrupo.objects.create(
            grupo=self.grupo, produto=self.produto, maquinas=10, operadores=20,
            minutos_por_maquina=400,
        )
        self.recife = Cidade.objects.create(
            nome="Recife", distancia_km=290, demanda=1000
        )
        DemandaCidadeProduto.objects.create(
            cidade=self.recife, produto=self.produto, demanda_maxima=1000
        )
        self.rodada = Rodada.objects.create(
            jogo=self.jogo, numero=1,
            fim=timezone.now() - timedelta(minutes=1), sorteio_evento=False,
        )
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=1,
            quantidade_planejada=1000,
        )
        Distribuicao.objects.create(
            grupo=self.grupo, produto=self.produto, cidade=self.recife, rodada=1,
            quantidade=1000, preco_unitario=Decimal("10"),
            custo_transporte=Decimal("0"),
        )

    def _registrar(self, **campos):
        padrao = {
            "nome": "Evento do professor", "tipo": "demanda",
            "modo_aplicacao": "percentual", "impacto_percentual": 0,
            "probabilidade": 0, "manual": True, "jogo": self.jogo,
        }
        padrao.update(campos)
        evento = Evento.objects.create(**padrao)
        EventoRodada.objects.create(
            rodada=1, jogo=self.jogo, evento=evento, manual=True
        )
        return evento

    def test_a_queda_de_demanda_manual_limita_a_venda(self):
        self._registrar(
            modo_aplicacao="absoluto", valor_absoluto=Decimal("-600")
        )

        call_command("fechar_rodadas", stdout=StringIO())

        envio = Distribuicao.objects.get(grupo=self.grupo, rodada=1)
        self.assertEqual(envio.quantidade_vendida, 400)

    def test_a_lista_da_rodada_traz_o_evento_do_professor(self):
        evento = self._registrar(impacto_percentual=-20)

        self.assertEqual(eventos_da_rodada(1, jogo_id=self.jogo.id), [evento])

    def test_a_turma_le_a_manchete_do_evento_do_professor(self):
        self._registrar(
            impacto_percentual=-20,
            frase_indicativa="A chuva esvaziou as feiras da região.",
        )
        self.rodada.fim = timezone.now() + timedelta(hours=1)
        self.rodada.save(update_fields=["fim"])
        ceo = User.objects.create_user(
            email_usuario="ceo-boletim@example.com", nome_usuario="CEO",
            password="pass", tipo_usuario="lider_grupo",
        )
        self.grupo.membros.add(ceo)
        self.client.force_login(ceo)

        resposta = self.client.get(reverse("painel_grupo"))

        self.assertContains(resposta, "A chuva esvaziou as feiras da região.")
