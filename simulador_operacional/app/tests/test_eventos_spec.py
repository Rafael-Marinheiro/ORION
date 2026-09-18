"""Os eventos do 8.4: manchete, probabilidade e sorteio ponderado."""

from collections import Counter
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Evento, EventoRodada, Grupo, Rodada, User
from app.views import sortear_evento


class SeedDosEventosTest(TestCase):
    def setUp(self):
        call_command("seed_dados_base")

    def test_sao_exatamente_os_seis_do_documento(self):
        nomes = set(Evento.objects.values_list("nome", flat=True))

        self.assertEqual(
            nomes,
            {
                "Greve de caminhoneiros",
                "Crise de abastecimento",
                "Boom de consumo",
                "Enchentes nas regiões",
                "Estabilidade econômica",
                "Superoferta agrícola",
            },
        )

    def test_probabilidades_somam_cem_por_cento(self):
        """8.4: "A soma total das probabilidades e de 100%"."""
        total = sum(Decimal(str(p)) for p in Evento.objects.values_list("probabilidade", flat=True))

        self.assertEqual(total, Decimal("100"))

    def test_cada_evento_tem_manchete(self):
        sem_manchete = Evento.objects.filter(frase_indicativa="").values_list("nome", flat=True)

        self.assertEqual(list(sem_manchete), [])

    def test_manchete_e_diferente_da_descricao(self):
        """Sao colunas distintas no 8.4: uma e noticia, a outra e mecanismo."""
        for evento in Evento.objects.all():
            self.assertNotEqual(evento.frase_indicativa, evento.descricao, evento.nome)

    def test_probabilidades_do_documento(self):
        esperado = {
            "Greve de caminhoneiros": Decimal("15"),
            "Crise de abastecimento": Decimal("20"),
            "Boom de consumo": Decimal("20"),
            "Enchentes nas regiões": Decimal("15"),
            "Estabilidade econômica": Decimal("15"),
            "Superoferta agrícola": Decimal("15"),
        }
        obtido = {
            e.nome: Decimal(str(e.probabilidade)) for e in Evento.objects.all()
        }

        self.assertEqual(obtido, esperado)


class SorteioPonderadoTest(TestCase):
    """O sorteio uniforme dava a mesma chance a eventos de 15% e de 20%."""

    def test_evento_mais_provavel_sai_mais(self):
        raro = Evento.objects.create(
            nome="Raro", tipo="demanda", impacto_percentual=1, probabilidade=1
        )
        comum = Evento.objects.create(
            nome="Comum", tipo="demanda", impacto_percentual=1, probabilidade=99
        )

        contagem = Counter()
        for rodada in range(1, 121):
            escolhido = sortear_evento(rodada)
            contagem[escolhido.nome] += 1

        self.assertGreater(contagem[comum.nome], contagem[raro.nome])
        # com 99 contra 1, o raro nao deve dominar nem por acaso
        self.assertLess(contagem[raro.nome], 30)

    def test_sem_probabilidade_configurada_nao_trava(self):
        Evento.objects.create(
            nome="Sem peso", tipo="demanda", impacto_percentual=1, probabilidade=0
        )

        self.assertIsNotNone(sortear_evento(1))


class BoletimNaTelaTest(TestCase):
    def test_manchete_aparece_para_o_aluno(self):
        user = User.objects.create_user(
            email_usuario="membro@teste.com", nome_usuario="Membro", password="senha123"
        )
        grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100"))
        grupo.membros.add(user)
        rodada = Rodada.objects.create(
            numero=1, fim=timezone.now() + timezone.timedelta(hours=1)
        )
        evento = Evento.objects.create(
            nome="Greve de caminhoneiros",
            frase_indicativa="O país enfrenta uma greve geral no setor de transporte rodoviário.",
            tipo="custo_transporte",
            impacto_percentual=30,
            probabilidade=15,
        )
        EventoRodada.objects.create(rodada=rodada.numero, jogo=None, evento=evento)
        self.client.force_login(user)

        html = self.client.get(reverse("ajuda")).content.decode()

        self.assertIn("O país enfrenta uma greve geral", html)
        self.assertIn("o-boletim", html)


class VariedadeDeEventosTest(TestCase):
    """O evento recente fica improvavel, nunca impossivel.

    Bloquear o evento recente achataria os pesos: medido com 3 eventos de
    pesos 60/30/10, um cooldown duro de 2 rodadas os transforma em 33/33/33.
    Reduzir o peso preserva a configuracao do professor.
    """

    def setUp(self):
        self.provavel = Evento.objects.create(
            nome="Provável", tipo="demanda", impacto_percentual=5, probabilidade=80
        )
        self.raro = Evento.objects.create(
            nome="Raro", tipo="demanda", impacto_percentual=5, probabilidade=20
        )

    def test_evento_da_rodada_anterior_perde_peso_mas_continua_possivel(self):
        EventoRodada.objects.create(rodada=1, evento=self.provavel)

        saiu_o_provavel = 0
        for rodada in range(2, 202):
            EventoRodada.objects.filter(rodada=rodada).delete()
            # cada sorteio enxerga a rodada 1 como anterior imediata
            EventoRodada.objects.filter(rodada__gt=1).delete()
            if sortear_evento(2).id == self.provavel.id:
                saiu_o_provavel += 1

        # sem penalidade sairia ~80%; com peso x0,05 cai para perto de 17%
        self.assertLess(saiu_o_provavel, 80)
        # mas nao e proibido: continua acontecendo
        self.assertGreater(saiu_o_provavel, 0)

    def test_evento_antigo_nao_sofre_penalidade(self):
        from app.services.eventos import _fator_de_repeticao

        recentes = {1: self.provavel.id}

        self.assertEqual(_fator_de_repeticao(self.provavel.id, recentes, 2), 0.05)
        self.assertEqual(_fator_de_repeticao(self.provavel.id, recentes, 3), 0.30)
        self.assertEqual(_fator_de_repeticao(self.provavel.id, recentes, 4), 0.65)
        # fora do alcance, peso cheio
        self.assertEqual(_fator_de_repeticao(self.provavel.id, recentes, 9), 1.0)

    def test_lacuna_de_rodada_nao_encurta_a_distancia(self):
        """Rodada sem evento nao pode fazer um evento antigo parecer recente."""
        from app.services.eventos import _fator_de_repeticao

        recentes = {2: self.provavel.id}

        # a rodada 5 esta a 3 de distancia da 2, mesmo sem evento em 3 e 4
        self.assertEqual(_fator_de_repeticao(self.provavel.id, recentes, 5), 0.65)

    def test_com_um_unico_evento_ele_sai_mesmo_penalizado(self):
        self.raro.delete()
        EventoRodada.objects.create(rodada=1, evento=self.provavel)

        self.assertEqual(sortear_evento(2).id, self.provavel.id)
