from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from .serializers import (
    GrupoSerializer,
    ResultadoFinanceiroSerializer,
    DecisaoSerializer,
    DistribuicaoSerializer,
    EventoSerializer,
    EventoRodadaSerializer,
    RodadaSerializer,
    CidadeSerializer,
    GameConfigSerializer,
    JogoSerializer,
    InvestimentoSerializer,
)
from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal
from .forms import (
    CustomUserCreationForm,
    DecisaoForm,
    DistribuicaoForm,
    RodadaForm,
    GrupoForm,
    ResultadoFilterForm,
)
from .models import (
    GameConfig,
    Grupo,
    Decisao,
    Distribuicao,
    Cidade,
    ResultadoFinanceiro,
    Evento,
    EventoRodada,
    Rodada,
    Jogo,
    Investimento,
)
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.pdfgen import canvas
import random
import logging
from django.utils import timezone
from django.db.models import Sum

logger = logging.getLogger('agendamentos')


def sortear_eventos(rodada):
    registros = EventoRodada.objects.filter(rodada=rodada)
    if registros.exists():
        return [r.evento for r in registros]

    eventos = list(Evento.objects.all())
    if not eventos:
        return []

    escolhidos = []
    total = sum(e.probabilidade for e in eventos)
    for _ in range(2):
        r = random.uniform(0, total)
        acum = 0
        escolha = eventos[-1]
        for e in eventos:
            acum += e.probabilidade
            if r <= acum:
                escolha = e
                break
        if escolha not in escolhidos:
            escolhidos.append(escolha)

    for evento in escolhidos:
        EventoRodada.objects.create(rodada=rodada, evento=evento)
    if escolhidos:
        logger.info('Eventos sorteados para rodada %s: %s', rodada, ', '.join(e.nome for e in escolhidos))
    else:
        logger.info('Nenhum evento sorteado para rodada %s', rodada)
    return escolhidos

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if getattr(user, "tipo_usuario", None) == "gamemaster" or user.is_superuser:
            return reverse_lazy("game_config")
        return reverse_lazy("painel_grupo")

class HomeView(TemplateView):
    template_name = 'home.html'
    # login_url = '/accounts/login/'

class AjudaView(TemplateView):
    """Página com tutoriais rápidos e perguntas frequentes."""
    template_name = 'ajuda.html'

@login_required
def home(request):
    return render(request, 'home.html')


class RegisterView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = 'registration/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')

    def test_func(self):
        return getattr(self.request.user, 'tipo_usuario', '') == 'gamemaster'


class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


from django.views.generic import UpdateView
from .models import GameConfig
from .forms import GameConfigForm


class GameConfigUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = GameConfig
    form_class = GameConfigForm
    template_name = 'game_config_form.html'
    success_url = reverse_lazy('home')


    permission_required = 'app.change_gameconfig'

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

    def get_object(self, queryset=None):
        obj, _ = GameConfig.objects.get_or_create(id=1)
        return obj


class RodadaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Rodada
    form_class = RodadaForm
    template_name = 'rodada_form.html'
    success_url = reverse_lazy('home')

    permission_required = 'app.add_rodada'

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()


class RankingView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'ranking.html'
    model = Grupo
    context_object_name = 'grupos'
    permission_required = 'app.view_resultadofinanceiro'

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

    def get_queryset(self):
        grupos = Grupo.objects.annotate(
            total_lucro=Sum('resultados__lucro'),
            total_envios=Sum('envios__quantidade'),
        )
        total_envios_all = (
            Distribuicao.objects.aggregate(total=Sum('quantidade'))['total'] or 0
        )
        for g in grupos:
            envios = g.total_envios or 0
            market_share = (envios / total_envios_all) if total_envios_all else 0
            capacidade = g.maquinas * g.capacidade_maquina
            eficiencia = (envios / capacidade) if capacidade else 0
            g.rank_score = (g.total_lucro or 0) + market_share * 1000 + eficiencia * 100
        return sorted(grupos, key=lambda x: x.rank_score, reverse=True)


class PainelGrupoView(LoginRequiredMixin, TemplateView):
    template_name = 'painel_grupo.html'

    def calcular_capacidade_producao(self, grupo):
        maquinas_operacionais = min(grupo.maquinas, grupo.trabalhadores // 2)
        return maquinas_operacionais * grupo.capacidade_maquina

    def get(self, request, *args, **kwargs):
        grupo = request.user.grupos.first()
        if not grupo:
            messages.error(request, "Você precisa criar ou entrar em um grupo.")
            return redirect("criar_grupo")
        membros = grupo.membros.count()
        if membros < 3 or membros > 6:
            messages.error(
                request, "O grupo deve possuir entre 3 e 6 participantes."
            )
            return redirect("criar_grupo")
        form = DecisaoForm()
        envio_form = DistribuicaoForm()
        decisoes = grupo.decisoes.all()
        envios = grupo.envios.select_related("cidade").all()
        resultados = grupo.resultados.all()
        ultima_vista = request.session.get("ultima_rodada_vista", 0)
        nova = resultados.order_by("-rodada").first()
        notificacao = None
        if nova and nova.rodada > ultima_vista:
            notificacao = f"Resultados da rodada {nova.rodada} disponíveis."
            request.session["ultima_rodada_vista"] = nova.rodada
        ultima = grupo.decisoes.first()
        rodada_atual = ultima.rodada + 1 if ultima else 1
        eventos = [er.evento for er in EventoRodada.objects.filter(rodada=rodada_atual)]
        capacidade_total = self.calcular_capacidade_producao(grupo)
        alerta = None
        if grupo.estoque < capacidade_total * 0.2:
            alerta = 'Risco de ruptura de estoque'
        elif grupo.estoque > capacidade_total:
            alerta = 'Risco de desperdício de estoque'
        return render(request, self.template_name, {
            'grupo': grupo,
            'decisoes': decisoes,
            'form': form,
            'envio_form': envio_form,
            'envios': envios,
            'resultados': resultados,
            'alerta': alerta,
            'eventos': eventos,
            'notificacao': notificacao,
        })

    def post(self, request, *args, **kwargs):
        grupo = request.user.grupos.first()
        if not grupo:
            messages.error(request, "Você precisa criar ou entrar em um grupo.")
            return redirect("criar_grupo")
        membros = grupo.membros.count()
        if membros < 3 or membros > 6:
            messages.error(
                request, "O grupo deve possuir entre 3 e 6 participantes."
            )
            return redirect("criar_grupo")
        if 'enviar_decisao' in request.POST:
            if request.user.tipo_usuario != 'lider_grupo' and not request.user.is_staff:
                messages.error(request, 'Apenas o Aluno CEO pode enviar decisões')
                return redirect('painel_grupo')
            form = DecisaoForm(request.POST)
            if form.is_valid():
                decisao = form.save(commit=False)
                decisao.grupo = grupo
                capacidade_total = self.calcular_capacidade_producao(grupo)
                if decisao.quantidade > capacidade_total:
                    decisao.quantidade = capacidade_total
                    messages.warning(
                        request,
                        'Quantidade de produção ajustada ao limite operacional.',
                    )
                if Decisao.objects.filter(grupo=grupo, rodada=decisao.rodada).exists():
                    messages.error(request, 'Decisão já enviada para esta rodada')
                    return redirect('painel_grupo')
                if Rodada.objects.filter(numero=decisao.rodada, fim__lt=timezone.now()).exists() or Rodada.objects.filter(numero=decisao.rodada, fechada=True).exists():
                    messages.error(request, 'Prazo encerrado para esta rodada')
                    return redirect('painel_grupo')

                eventos = [er.evento for er in EventoRodada.objects.filter(rodada=decisao.rodada)]
                custo_prod = Decimal(decisao.quantidade) * Decimal('5')
                for evento in eventos:
                    if evento.tipo == 'custo_producao':
                        custo_prod *= Decimal(1 + evento.impacto_percentual / 100)
                decisao.save()
                if grupo.capital < custo_prod:
                    penalidade = custo_prod * Decimal('0.02')
                    grupo.capital -= penalidade
                    grupo.save()
                    rf, _ = ResultadoFinanceiro.objects.get_or_create(grupo=grupo, rodada=decisao.rodada)
                    rf.custos += penalidade
                    rf.saldo_caixa = grupo.capital
                    rf.lucro = rf.receita - rf.custos
                    rf.save()
                    messages.error(request, 'Capital insuficiente para produção. Penalidade aplicada.')
                else:
                    grupo.capital -= custo_prod
                    grupo.estoque += decisao.quantidade
                    grupo.save()
                    rf, _ = ResultadoFinanceiro.objects.get_or_create(
                        grupo=grupo, rodada=decisao.rodada
                    )
                    rf.custos += custo_prod
                    rf.saldo_caixa = grupo.capital
                    rf.lucro = rf.receita - rf.custos
                    rf.save()
                    messages.success(request, 'Decisão registrada')
                    return redirect('painel_grupo')
        elif 'enviar_envio' in request.POST:
            if request.user.tipo_usuario != 'lider_grupo' and not request.user.is_staff:
                messages.error(request, 'Apenas o Aluno CEO pode enviar distribuições')
                return redirect('painel_grupo')
            envio_form = DistribuicaoForm(request.POST)
            if envio_form.is_valid():
                envio = envio_form.save(commit=False)
                envio.grupo = grupo
                if Distribuicao.objects.filter(grupo=grupo, rodada=envio.rodada).exists():
                    messages.error(request, 'Envio já realizado nesta rodada')
                    return redirect('painel_grupo')
                if Rodada.objects.filter(numero=envio.rodada, fim__lt=timezone.now()).exists() or Rodada.objects.filter(numero=envio.rodada, fechada=True).exists():
                    messages.error(request, 'Prazo encerrado para esta rodada')
                    return redirect('painel_grupo')

                eventos = [er.evento for er in EventoRodada.objects.filter(rodada=envio.rodada)]
                if envio.quantidade > grupo.estoque:
                    penalidade = envio.quantidade * envio.preco_unitario * Decimal('0.05')
                    grupo.capital -= penalidade
                    grupo.save()
                    rf, _ = ResultadoFinanceiro.objects.get_or_create(grupo=grupo, rodada=envio.rodada)
                    rf.custos += penalidade
                    rf.saldo_caixa = grupo.capital
                    rf.lucro = rf.receita - rf.custos
                    rf.save()
                    messages.error(request, 'Estoque insuficiente. Penalidade aplicada.')
                else:
                    custo = Decimal(envio.cidade.distancia_km) * envio.quantidade * Decimal('0.1')
                    for evento in eventos:
                        if evento.tipo == 'custo_transporte':
                            custo *= Decimal(1 + evento.impacto_percentual / 100)
                    envio.custo_transporte = custo
                    envio.save()
                    grupo.estoque -= envio.quantidade
                    vendas_realizadas = min(envio.quantidade, envio.cidade.demanda)
                    if vendas_realizadas < envio.quantidade:
                        messages.warning(
                            request,
                            'Parte da remessa não foi vendida por falta de demanda.',
                        )
                    receita = vendas_realizadas * envio.preco_unitario
                    for evento in eventos:
                        if evento.tipo == 'demanda':
                            receita *= Decimal(1 + evento.impacto_percentual / 100)
                    grupo.capital += receita - custo
                    grupo.save()
                    rf, _ = ResultadoFinanceiro.objects.get_or_create(
                        grupo=grupo, rodada=envio.rodada
                    )
                    rf.receita += receita
                    rf.custos += custo
                    rf.lucro = rf.receita - rf.custos
                    rf.saldo_caixa = grupo.capital
                    rf.save()
                    messages.success(request, 'Distribuição registrada')
                    return redirect('painel_grupo')
        form = DecisaoForm()
        envio_form = DistribuicaoForm()
        decisoes = grupo.decisoes.all()
        envios = grupo.envios.select_related("cidade").all()
        resultados = grupo.resultados.all()
        ultima_vista = request.session.get("ultima_rodada_vista", 0)
        nova = resultados.order_by("-rodada").first()
        notificacao = None
        if nova and nova.rodada > ultima_vista:
            notificacao = f"Resultados da rodada {nova.rodada} disponíveis."
            request.session["ultima_rodada_vista"] = nova.rodada
        ultima = grupo.decisoes.first()
        rodada_atual = ultima.rodada + 1 if ultima else 1
        eventos = [er.evento for er in EventoRodada.objects.filter(rodada=rodada_atual)]
        capacidade_total = self.calcular_capacidade_producao(grupo)
        alerta = None
        if grupo.estoque < capacidade_total * 0.2:
            alerta = 'Risco de ruptura de estoque'
        elif grupo.estoque > capacidade_total:
            alerta = 'Risco de desperdício de estoque'
        return render(request, self.template_name, {
            'grupo': grupo,
            'decisoes': decisoes,
            'form': form,
            'envio_form': envio_form,
            'envios': envios,
            'resultados': resultados,
            'alerta': alerta,
            'eventos': eventos,
            'notificacao': notificacao,
        })


class GrupoViewSet(viewsets.ModelViewSet):
    queryset = Grupo.objects.all()
    serializer_class = GrupoSerializer


class DecisaoViewSet(viewsets.ModelViewSet):
    queryset = Decisao.objects.all()
    serializer_class = DecisaoSerializer


class DistribuicaoViewSet(viewsets.ModelViewSet):
    queryset = Distribuicao.objects.all()
    serializer_class = DistribuicaoSerializer


class ResultadoFinanceiroViewSet(viewsets.ModelViewSet):
    queryset = ResultadoFinanceiro.objects.all()
    serializer_class = ResultadoFinanceiroSerializer


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer


class EventoRodadaViewSet(viewsets.ModelViewSet):
    queryset = EventoRodada.objects.all()
    serializer_class = EventoRodadaSerializer


class RodadaViewSet(viewsets.ModelViewSet):
    queryset = Rodada.objects.all()
    serializer_class = RodadaSerializer


class CidadeViewSet(viewsets.ModelViewSet):
    queryset = Cidade.objects.all()
    serializer_class = CidadeSerializer


class GameConfigViewSet(viewsets.ModelViewSet):
    queryset = GameConfig.objects.all()
    serializer_class = GameConfigSerializer


class JogoViewSet(viewsets.ModelViewSet):
    queryset = Jogo.objects.all()
    serializer_class = JogoSerializer


class InvestimentoViewSet(viewsets.ModelViewSet):
    queryset = Investimento.objects.all()
    serializer_class = InvestimentoSerializer

    def create(self, request, *args, **kwargs):
        grupo_id = request.data.get('grupo')
        if grupo_id:
            resultados = (
                ResultadoFinanceiro.objects.filter(grupo_id=grupo_id)
                .order_by('-rodada')[:2]
            )
            if len(resultados) == 2 and all(r.saldo_caixa < 0 for r in resultados):
                return Response(
                    {
                        'detail': 'Investimentos bloqueados por fluxo de caixa negativo.'
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return super().create(request, *args, **kwargs)


class RankingAPIView(generics.ListAPIView):
    serializer_class = GrupoSerializer

    def get_queryset(self):
        grupos = Grupo.objects.annotate(
            total_lucro=Sum('resultados__lucro'),
            total_envios=Sum('envios__quantidade'),
        )
        total_envios_all = (
            Distribuicao.objects.aggregate(total=Sum('quantidade'))['total'] or 0
        )
        ranking = []
        for g in grupos:
            envios = g.total_envios or 0
            market_share = (envios / total_envios_all) if total_envios_all else 0
            capacidade = g.maquinas * g.capacidade_maquina
            eficiencia = (envios / capacidade) if capacidade else 0
            score = (g.total_lucro or 0) + market_share * 1000 + eficiencia * 100
            ranking.append((score, g))
        return [g for score, g in sorted(ranking, key=lambda x: x[0], reverse=True)]


class GrupoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Grupo
    template_name = "grupo_list.html"
    context_object_name = "grupos"
    permission_required = "app.view_grupo"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()


class GrupoCreateView(LoginRequiredMixin, CreateView):
    model = Grupo
    form_class = GrupoForm
    template_name = "grupo_form.html"
    success_url = reverse_lazy("painel_grupo")

    def form_valid(self, form):
        grupo = form.save(commit=False)
        config, _ = GameConfig.objects.get_or_create(id=1)
        grupo.capital = config.capital_inicial
        grupo.estoque = config.estoque_inicial
        grupo.maquinas_a = config.maquinas_iniciais_a
        grupo.maquinas_b = config.maquinas_iniciais_b
        grupo.maquinas_c = config.maquinas_iniciais_c
        grupo.maquinas = (
            config.maquinas_iniciais_a
            + config.maquinas_iniciais_b
            + config.maquinas_iniciais_c
        )
        grupo.trabalhadores = config.trabalhadores_iniciais
        grupo.capacidade_maquina = config.capacidade_maquina
        grupo.save()
        form.save_m2m()
        if self.request.user not in grupo.membros.all():
            grupo.membros.add(self.request.user)
        return redirect(self.success_url)


class GrupoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Grupo
    form_class = GrupoForm
    template_name = "grupo_form.html"
    success_url = reverse_lazy("lista_grupos")
    permission_required = "app.change_grupo"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()


class RelatoriosView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "financeiro/relatorios.html"
    permission_required = "app.view_resultadofinanceiro"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()

    def get(self, request, *args, **kwargs):
        form = ResultadoFilterForm(request.GET or None)
        resultados = ResultadoFinanceiro.objects.select_related("grupo")
        if form.is_valid():
            if form.cleaned_data.get("rodada"):
                resultados = resultados.filter(rodada=form.cleaned_data["rodada"])
            if form.cleaned_data.get("grupo"):
                resultados = resultados.filter(grupo=form.cleaned_data["grupo"])
        return render(
            request,
            self.template_name,
            {"resultados": resultados, "form": form},
        )


@login_required
def export_resultados_pdf(request):
    rodada = request.GET.get("rodada")
    grupo_id = request.GET.get("grupo")
    qs = ResultadoFinanceiro.objects.select_related("grupo")
    if rodada:
        qs = qs.filter(rodada=rodada)
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=resultados.pdf"
    p = canvas.Canvas(response)
    y = 800
    p.drawString(100, y, "Resultados Financeiros")
    y -= 20
    for r in qs:
        p.drawString(
            100,
            y,
            f"Grupo {r.grupo.nome} - Rodada {r.rodada} - Lucro {r.lucro}",
        )
        y -= 20
        if y < 50:
            p.showPage()
            y = 800
    p.showPage()
    p.save()
    return response


@login_required
def export_resultados_excel(request):
    rodada = request.GET.get("rodada")
    grupo_id = request.GET.get("grupo")
    qs = ResultadoFinanceiro.objects.select_related("grupo")
    if rodada:
        qs = qs.filter(rodada=rodada)
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)
    wb = Workbook()
    ws = wb.active
    ws.append(["Grupo", "Rodada", "Receita", "Custos", "Lucro", "Caixa"])
    for r in qs:
        ws.append(
            [
                r.grupo.nome,
                r.rodada,
                float(r.receita),
                float(r.custos),
                float(r.lucro),
                float(r.saldo_caixa),
            ]
        )
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=resultados.xlsx"
    wb.save(response)
    return response
