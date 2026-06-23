from .models import Notificacao


def notificacoes(request):
  if not request.user.is_authenticated:
    return {}
  try:
    esteticista = request.user.esteticista
    notificacoes = Notificacao.objects.filter(
      esteticista=esteticista, lida=False
    ).order_by("-criada_em")[:5]
    return {"notificacoes": notificacoes}
  except Exception:
    return {}
