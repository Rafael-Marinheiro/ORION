"""Contexto do trilho de rodada exibido no topo das paginas autenticadas."""

from app.models import Decisao, EventoRodada
from app.views import obter_grupo_do_usuario, obter_rodada_ativa


def trilho_rodada(request):
    """Rodada corrente, evento e estado da submissao do grupo do usuario.

    Devolve dicionario vazio para visitantes, para nao custar consulta nem
    renderizar o trilho nas telas publicas.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}

    grupo = obter_grupo_do_usuario(user)
    rodada = obter_rodada_ativa(grupo)

    contexto = {"mostrar_trilho": True, "rodada_corrente": rodada}
    if rodada is None:
        return contexto

    # Uma rodada pode ter mais de um evento desde 25/09/2026: o sorteado do
    # 8.2 e o que o professor determinou na abertura.
    contexto["eventos_correntes"] = [
        evento_rodada.evento
        for evento_rodada in EventoRodada.objects.filter(
            rodada=rodada.numero, jogo=rodada.jogo
        )
        .select_related("evento")
        .order_by("manual", "id")
    ]
    contexto["submissao_realizada"] = bool(
        grupo and Decisao.objects.filter(grupo=grupo, rodada=rodada.numero).exists()
    )
    return contexto
