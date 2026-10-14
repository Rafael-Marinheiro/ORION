# -*- coding: utf-8 -*-
"""Pool estendido de eventos, e duracao maior que uma rodada.

O 8.4 e a tabela fechada do documento e continua sendo o padrao: turma sem
configuracao explicita sorteia exatamente os seis eventos de la. O pool
estendido e opcional por turma.

O 8.2 ressalva "reversao automatica dos impactos na rodada seguinte (salvo
eventos recorrentes)". O campo `duracao_rodadas` existia e so era lido para
eventos de estado -- um evento percentual de tres rodadas durava uma.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone

from app.models import Cidade, Evento, GameConfig, Jogo, Rodada
from app.services.eventos import (
    eventos_da_rodada,
    fator_percentual,
    sortear_evento,
)


def _rodada(jogo, numero, **extra):
    return Rodada.objects.get_or_create(
        jogo=jogo, numero=numero,
        defaults={"fim": timezone.now() + timedelta(hours=2), **extra},
    )[0]


def _evento(nome, **extra):
    campos = {
        "tipo": "demanda",
        "modo_aplicacao": "percentual",
        "impacto_percentual": 10,
        "probabilidade": 50,
    }
    campos.update(extra)
    return Evento.objects.create(nome=nome, **campos)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class PoolEstendidoTest(TestCase):
    def setUp(self):
        self.config = GameConfig.objects.create(numero_rodadas=4)
        self.jogo = Jogo.objects.create(nome="Turma A", config=self.config)
        _rodada(self.jogo, 1)
        self.do_documento = _evento("Boom de consumo")
        self.estendido = _evento("Retracao de consumo", extensao=True,
                                 impacto_percentual=-15)

    def test_sem_a_opcao_so_sorteia_a_tabela_do_documento(self):
        sorteados = set()
        for numero in range(1, 40):
            _rodada(self.jogo, numero)
            evento = sortear_evento(numero, self.jogo.id)
            if evento:
                sorteados.add(evento.nome)

        self.assertEqual(sorteados, {"Boom de consumo"})

    def test_com_a_opcao_o_estendido_entra_no_sorteio(self):
        self.config.eventos_estendidos = True
        self.config.save(update_fields=["eventos_estendidos"])

        sorteados = set()
        for numero in range(1, 60):
            _rodada(self.jogo, numero)
            evento = sortear_evento(numero, self.jogo.id)
            if evento:
                sorteados.add(evento.nome)

        self.assertIn("Retracao de consumo", sorteados)
        self.assertIn("Boom de consumo", sorteados)

    def test_a_opcao_de_uma_turma_nao_vaza_para_a_outra(self):
        self.config.eventos_estendidos = True
        self.config.save(update_fields=["eventos_estendidos"])
        outra = Jogo.objects.create(
            nome="Turma B", config=GameConfig.objects.create(numero_rodadas=4)
        )

        sorteados = set()
        for numero in range(1, 40):
            _rodada(outra, numero)
            evento = sortear_evento(numero, outra.id)
            if evento:
                sorteados.add(evento.nome)

        self.assertEqual(sorteados, {"Boom de consumo"})


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class EventoRecorrenteTest(TestCase):
    """8.2: "salvo eventos recorrentes"."""

    def setUp(self):
        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=6)
        )
        self.tarifa = _evento(
            "Tarifacao externa", tipo="custo_producao", extensao=True,
            impacto_percentual=15, duracao_rodadas=3,
        )
        _rodada(self.jogo, 1, sorteio_evento=False)
        from app.models import EventoRodada
        EventoRodada.objects.create(
            rodada=1, jogo=self.jogo, evento=self.tarifa, manual=True
        )

    def test_o_evento_de_tres_rodadas_vale_nas_tres(self):
        for numero in (1, 2, 3):
            nomes = [e.nome for e in eventos_da_rodada(numero, self.jogo.id)]
            self.assertIn("Tarifacao externa", nomes, f"rodada {numero}")

    def test_e_some_na_quarta(self):
        nomes = [e.nome for e in eventos_da_rodada(4, self.jogo.id)]

        self.assertNotIn("Tarifacao externa", nomes)

    def test_o_custo_continua_majorado_na_segunda_rodada(self):
        fator = fator_percentual(
            eventos_da_rodada(2, self.jogo.id), "custo_producao"
        )

        self.assertEqual(fator, Decimal("1.15"))

    def test_evento_de_uma_rodada_nao_atravessa(self):
        """Os seis do 8.4 tem duracao 1 e nao podem mudar de comportamento."""
        from app.models import EventoRodada
        boom = _evento("Boom de consumo", duracao_rodadas=1)
        EventoRodada.objects.create(
            rodada=2, jogo=self.jogo, evento=boom, manual=True
        )

        nomes = [e.nome for e in eventos_da_rodada(3, self.jogo.id)]

        self.assertNotIn("Boom de consumo", nomes)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class SeedDoPoolTest(TestCase):
    def test_o_seed_cria_os_dois_catalogos_e_as_probabilidades_fecham(self):
        from django.core.management import call_command

        call_command("seed_dados_base")

        documento = Evento.objects.filter(manual=False, extensao=False)
        estendidos = Evento.objects.filter(manual=False, extensao=True)
        self.assertEqual(documento.count(), 6)
        self.assertEqual(estendidos.count(), 10)
        self.assertEqual(
            sum(e.probabilidade for e in documento), 100
        )
        self.assertEqual(
            sum(e.probabilidade for e in estendidos), 100
        )

    def test_o_seed_preserva_o_evento_manual_do_professor(self):
        from django.core.management import call_command

        jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=4)
        )
        proprio = _evento("Feira regional", manual=True, jogo=jogo)
        Cidade.objects.create(nome="Recife", distancia_km=290, demanda=4000)

        call_command("seed_dados_base")

        self.assertTrue(Evento.objects.filter(id=proprio.id).exists())


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class BloqueioDeProducaoTest(TestCase):
    """O fechamento tambem para a fabrica, nao so a tela.

    `bloqueio_producao` era verificado apenas no registro da ordem pelo
    painel. A ordem registrada antes do evento entrar era produzida no
    fechamento assim mesmo: a tela dizia que a producao estava bloqueada e
    o resultado mostrava producao.
    """

    def setUp(self):
        from app.models import (
            CapacidadeProdutoGrupo,
            EstoqueMateriaPrima,
            MateriaPrima,
            Producao,
            Produto,
            ComposicaoProduto,
        )

        self.jogo = Jogo.objects.create(
            nome="Turma A", config=GameConfig.objects.create(numero_rodadas=4)
        )
        from app.models import Grupo
        self.grupo = Grupo.objects.create(
            nome="Equipe Vega", jogo=self.jogo, capital=Decimal("1000000")
        )
        self.produto = Produto.objects.create(
            codigo="A", nome="Produto A", tempo_producao_min=10
        )
        mp = MateriaPrima.objects.create(
            codigo="MP1", nome="MP1", preco_unitario=Decimal("1")
        )
        ComposicaoProduto.objects.create(
            produto=self.produto, materia_prima=mp,
            quantidade_por_unidade=Decimal("1"),
        )
        EstoqueMateriaPrima.objects.create(
            grupo=self.grupo, materia_prima=mp, quantidade_kg=Decimal("10000")
        )
        CapacidadeProdutoGrupo.objects.create(
            grupo=self.grupo, produto=self.produto, maquinas=15,
            operadores=30, minutos_por_maquina=400,
        )
        Producao.objects.create(
            grupo=self.grupo, produto=self.produto, rodada=1,
            quantidade_planejada=100,
        )
        _rodada(self.jogo, 1)

    def _executar(self, eventos):
        from app.services.producao import executar_producao

        return executar_producao(grupo=self.grupo, rodada=1, eventos=eventos)

    def test_sem_evento_a_ordem_e_produzida(self):
        from app.models import Producao

        self._executar([])

        ordem = Producao.objects.get(grupo=self.grupo, rodada=1)
        self.assertEqual(ordem.quantidade_produzida, 100)

    def test_o_apagao_zera_a_producao_da_rodada(self):
        from app.models import Producao

        apagao = _evento(
            "Apagao na regiao", tipo="greve", modo_aplicacao="estado",
            efeito_estado="bloqueio_producao", impacto_percentual=0,
            extensao=True,
        )

        _, ajustes = self._executar([apagao])

        ordem = Producao.objects.get(grupo=self.grupo, rodada=1)
        self.assertEqual(ordem.quantidade_produzida, 0)
        self.assertEqual(ajustes[0]["limitador"], "produção bloqueada por evento")
