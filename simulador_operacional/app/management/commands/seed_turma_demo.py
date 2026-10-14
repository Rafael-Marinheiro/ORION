# -*- coding: utf-8 -*-
"""Monta uma turma de demonstracao do zero, pronta para abrir a primeira rodada.

Serve para dois usos que ate agora dependiam de montar tudo a mao:

- ensaio antes da aula, para o professor percorrer o fluxo inteiro sem
  tocar na turma de verdade;
- base limpa depois de auditoria, sem precisar apagar o que ja existe.

`--limpar` remove SOMENTE a turma de mesmo nome e o que pende dela. Nao
existe opcao de limpar o banco inteiro, de proposito: um comando que apaga
turma alheia por descuido nao tem como ser desfeito em sala.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app.models import (
    CEOGrupoRodada,
    GameConfig,
    Grupo,
    Jogo,
    Rodada,
    User,
    default_ranking_pesos,
)
from app.services.producao import garantir_capacidades_grupo

NOME_PADRAO = "Turma Demo"

# Tres equipes de tres alunos: o 5 exige de 3 a 6 participantes, e tres
# equipes ja produzem disputa por demanda nas pracas sem encher a tela.
EQUIPES = [
    ("Equipe Vega", ["Ana", "Bruno", "Carla"]),
    ("Equipe Lira", ["Diego", "Elisa", "Fabio"]),
    ("Equipe Rigel", ["Gabriela", "Hugo", "Iara"]),
]


class Command(BaseCommand):
    help = "Cria uma turma de demonstracao completa, pronta para a rodada 1."

    def add_arguments(self, parser):
        parser.add_argument("--nome", default=NOME_PADRAO)
        parser.add_argument(
            "--rodadas", type=int, default=4,
            help="Numero de rodadas do ciclo (5: entre 3 e 12).",
        )
        parser.add_argument(
            "--senha", default=None,
            help="Senha dos alunos. Sem isto, uma e gerada e impressa.",
        )
        parser.add_argument(
            "--limpar", action="store_true",
            help="Apaga antes a turma de mesmo nome, se existir.",
        )
        parser.add_argument(
            "--abrir-rodada", action="store_true",
            help="Ja deixa a rodada 1 aberta, com prazo de 2 horas.",
        )

    @transaction.atomic
    def handle(self, *args, **opcoes):
        nome = opcoes["nome"]
        rodadas = opcoes["rodadas"]
        if not 3 <= rodadas <= 12:
            self.stderr.write("O 5 limita o ciclo a 3-12 rodadas.")
            return

        if opcoes["limpar"]:
            self.remover_turma(nome)

        if Jogo.objects.filter(nome=nome).exists():
            self.stderr.write(
                f'Ja existe a turma "{nome}". Use --limpar para recriar.'
            )
            return

        # O catalogo do 6, 7, 8 e 9 e comum a todas as turmas.
        call_command("seed_dados_base")

        senha = opcoes["senha"] or User.objects.make_random_password(length=14)

        config = GameConfig.objects.create(
            numero_rodadas=rodadas,
            ranking_pesos=default_ranking_pesos(),
        )
        jogo = Jogo.objects.create(nome=nome, config=config)

        criados = []
        for indice, (nome_grupo, integrantes) in enumerate(EQUIPES, start=1):
            grupo = Grupo.objects.create(
                nome=nome_grupo,
                jogo=jogo,
                capital=config.capital_inicial,
                estoque=config.estoque_inicial,
                maquinas_a=config.maquinas_iniciais_a,
                maquinas_b=config.maquinas_iniciais_b,
                maquinas_c=config.maquinas_iniciais_c,
                maquinas=(
                    config.maquinas_iniciais_a
                    + config.maquinas_iniciais_b
                    + config.maquinas_iniciais_c
                ),
                trabalhadores=config.trabalhadores_iniciais,
            )
            lider = None
            for ordem, primeiro_nome in enumerate(integrantes):
                usuario = User.objects.create_user(
                    email_usuario=(
                        f"{primeiro_nome.lower()}{indice}@demo.orion"
                    ),
                    nome_usuario=f"{primeiro_nome} ({nome_grupo})",
                    password=senha,
                    # 3: o CEO e "o unico autorizado a submeter".
                    tipo_usuario="lider_grupo" if ordem == 0 else "membro_grupo",
                )
                grupo.membros.add(usuario)
                if ordem == 0:
                    lider = usuario
            grupo.lider = lider
            grupo.save()
            # 13.4: o parque de largada existe antes de alguem abrir o painel.
            garantir_capacidades_grupo(grupo)
            criados.append((grupo, lider))

        rodada = None
        if opcoes["abrir_rodada"]:
            rodada = Rodada.objects.create(
                jogo=jogo,
                numero=1,
                fim=timezone.now() + timedelta(hours=2),
            )
            for grupo, lider in criados:
                CEOGrupoRodada.objects.create(
                    grupo=grupo, rodada=1, usuario=lider
                )

        self.stdout.write(self.style.SUCCESS(f'Turma "{nome}" criada.'))
        self.stdout.write(f"  config {config.id} - {rodadas} rodadas")
        for grupo, lider in criados:
            self.stdout.write(
                f"  {grupo.nome}: {grupo.membros.count()} integrantes, "
                f"CEO {lider.email_usuario}"
            )
        if rodada:
            self.stdout.write(
                f"  rodada 1 aberta, prazo {rodada.fim:%d/%m/%Y %H:%M}"
            )
        if not opcoes["senha"]:
            self.stdout.write(
                self.style.WARNING(f"  senha dos alunos: {senha}")
            )

    def remover_turma(self, nome):
        """Apaga a turma e o que pende dela, sem tocar em outra."""
        jogo = Jogo.objects.filter(nome=nome).first()
        if not jogo:
            return
        ids = list(
            User.objects.filter(grupos__jogo=jogo)
            .distinct()
            .values_list("pk", flat=True)
        )
        total_usuarios = len(ids)
        User.objects.filter(pk__in=ids).delete()
        config = jogo.config
        jogo.delete()
        # A config so some se nao sobrou turma usando ela.
        if config and not config.jogos.exists() and config.id != 1:
            config.delete()
        self.stdout.write(
            f'Turma "{nome}" removida ({total_usuarios} usuários).'
        )
