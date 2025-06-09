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
from rest_framework import viewsets, generics
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


def sortear_evento(rodada):
    try:
        return EventoRodada.objects.get(rodada=rodada).evento
    except EventoRodada.DoesNotExist:
        eventos = list(Evento.objects.all())
        if not eventos:
            return None
        total = sum(e.probabilidade for e in eventos)
        r = random.uniform(0, total)
        acum = 0
        escolhida = eventos[-1]
        for e in eventos:
            acum += e.probabilidade
            if r <= acum:
                escolhida = e
                break
        EventoRodada.objects.create(rodada=rodada, evento=escolhida)
        return escolhida

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')

class HomeView(TemplateView):
    template_name = 'home.html'
    # login_url = '/accounts/login/'

class AjudaView(TemplateView):
    """Página com tutoriais rápidos e perguntas frequentes."""
    template_name = 'ajuda.html'

@login_required
def home(request):
    return render(request, 'home.html')


class RegisterView(CreateView):
    template_name = 'registration/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')


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


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
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
        return Grupo.objects.order_by('-capital')


class PainelGrupoView(LoginRequiredMixin, TemplateView):
    template_name = 'painel_grupo.html'

    def get(self, request, *args, **kwargs):
        grupo, created = Grupo.objects.get_or_create(nome=request.user.nome_usuario)
        grupo.membros.add(request.user)
        if created:
            config, _ = GameConfig.objects.get_or_create(id=1)
            grupo.capital = config.capital_inicial
            grupo.estoque = config.estoque_inicial
            grupo.maquinas = config.maquinas_iniciais
            grupo.capacidade_maquina = config.capacidade_maquina
            grupo.save()
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
        evento = sortear_evento(rodada_atual)
        capacidade_total = grupo.maquinas * grupo.capacidade_maquina
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
            'evento': evento,
            'notificacao': notificacao,
        })

    def post(self, request, *args, **kwargs):
        grupo, _ = Grupo.objects.get_or_create(nome=request.user.nome_usuario)
        grupo.membros.add(request.user)
        if 'enviar_decisao' in request.POST:
            form = DecisaoForm(request.POST)
            if form.is_valid():
                decisao = form.save(commit=False)
                decisao.grupo = grupo
                evento = sortear_evento(decisao.rodada)
                custo_prod = Decimal(decisao.quantidade) * Decimal('5')
                if evento and evento.tipo == 'custo_producao':
                    custo_prod *= Decimal(1 + evento.impacto_percentual / 100)
                decisao.save()
                if grupo.capital < custo_prod:
                    messages.error(request, 'Capital insuficiente para produção')
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
            envio_form = DistribuicaoForm(request.POST)
            if envio_form.is_valid():
                envio = envio_form.save(commit=False)
                envio.grupo = grupo
                evento = sortear_evento(envio.rodada)
                if envio.quantidade > grupo.estoque:
                    messages.error(request, 'Estoque insuficiente')
                else:
                    custo = Decimal(envio.cidade.distancia_km) * envio.quantidade * Decimal('0.1')
                    if evento and evento.tipo == 'custo_transporte':
                        custo *= Decimal(1 + evento.impacto_percentual / 100)
                    envio.custo_transporte = custo
                    envio.save()
                    grupo.estoque -= envio.quantidade
                    receita = envio.quantidade * envio.preco_unitario
                    if evento and evento.tipo == 'demanda':
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
        evento = sortear_evento(rodada_atual)
        capacidade_total = grupo.maquinas * grupo.capacidade_maquina
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
            'evento': evento,
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


class RankingAPIView(generics.ListAPIView):
    queryset = Grupo.objects.order_by("-capital")
    serializer_class = GrupoSerializer


class GrupoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Grupo
    template_name = "grupo_list.html"
    context_object_name = "grupos"
    permission_required = "app.view_grupo"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()


class GrupoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Grupo
    form_class = GrupoForm
    template_name = "grupo_form.html"
    success_url = reverse_lazy("lista_grupos")
    permission_required = "app.add_grupo"

    def has_permission(self):
        return self.request.user.is_staff or super().has_permission()


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
