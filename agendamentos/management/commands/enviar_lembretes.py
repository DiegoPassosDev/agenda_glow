from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from agendamentos.models import Agendamento, Notificacao
import requests
import re

def formatar_telefone(telefone: str) -> str:
  apenas_numeros = re.sub(r'\D', '', telefone)
  if apenas_numeros.startswith('55') and len(apenas_numeros) >= 12:
    return apenas_numeros
  return '55' + apenas_numeros

def enviar_whatsapp(telefone: str, mensagem: str) -> dict:
  base_url = settings.EVOLUTION_API_URL.rstrip('/')
  api_key = settings.EVOLUTION_API_KEY
  instancia = settings.EVOLUTION_INSTANCE_NAME

  url = f"{base_url}/message/sendText/{instancia}"
  headers = {"Content-Type": "application/json", "apikey": api_key}
  payload = {"number": formatar_telefone(telefone), "textMessage": {"text": mensagem}}

  try:
    response = requests.post(
      url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    return {"sucesso": True, "resposta": response.json()}
  except requests.exceptions.Timeout:
    return {"sucesso": False, "resposta": "Timeout: Evolution API não respondeu em 15s"}
  except requests.exceptions.ConnectionError:
    return {"sucesso": False, "resposta": "Erro de conexão: Evolution API está rodando? (http://localhost:8080)"}
  except requests.exceptions.HTTPError:
    return {"sucesso": False, "resposta": f"Erro HTTP {response.status_code}: {response.text}"}
  except requests.exceptions.RequestException as e:
    return {"sucesso": False, "resposta": str(e)}

class Command(BaseCommand):
  help = "Envia lembretes por WhatsApp (Evolution API) para clientes e esteticistas"

  def add_arguments(self, parser):
    parser.add_argument('--minutos', type=int, default=60,
                        help='Minutos de antecedência (padrão: 60)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Simula sem enviar')

  def handle(self, *args, **options):
    antecedencia = options['minutos']
    dry_run = options['dry_run']
    agora = timezone.now()

    if dry_run:
      self.stdout.write(self.style.WARNING(
        '⚠️  MODO DRY-RUN: nenhuma mensagem será enviada.\n'))

    agendamentos_proximos = Agendamento.objects.filter(
      data_hora__gte=agora + timedelta(minutes=antecedencia - 1),
      data_hora__lte=agora + timedelta(minutes=antecedencia + 1),
      status__in=['agendado', 'confirmado'],
    ).select_related('esteticista', 'cliente', 'servico')

    if not agendamentos_proximos.exists():
      self.stdout.write(
        f'Nenhum agendamento para os próximos {antecedencia} minutos.')
      return

    enviados = erros = 0

    for ag in agendamentos_proximos:

      if Notificacao.objects.filter(agendamento=ag, tipo='lembrete').exists():
        self.stdout.write(
          f'  ⏭  Já enviado para {ag.cliente.nome} — pulando.')
        continue

      data_fmt = ag.data_hora.strftime('%d/%m/%Y')
      hora_fmt = ag.data_hora.strftime('%H:%M')

      msg_cliente = (
        f"Olá, *{ag.cliente.nome.title()}*! 👋\n\n"
        f"Lembrete do seu agendamento na *Agenda Glow*:\n\n"
        f"📅 *Data:* {data_fmt}\n"
        f"⏰ *Horário:* {hora_fmt}\n"
        f"💆 *Serviço:* {ag.servico.nome.title()}\n"
        f"👩 *Profissional:* {ag.esteticista}\n\n"
        f"Precisa cancelar ou reagendar? Entre em contato conosco. 😊"
      )

      msg_esteticista = (
        f"⏰ *Atendimento em {antecedencia} minutos!*\n\n"
        f"👤 *Cliente:* {ag.cliente.nome.title()}\n"
        f"💆 *Serviço:* {ag.servico.nome.title()}\n"
        f"🕐 *Horário:* {hora_fmt}\n"
        f"📞 *Telefone:* {ag.cliente.telefone}"
      )

      if ag.cliente.telefone:
        if dry_run:
          self.stdout.write(self.style.SUCCESS(
            f'\n[DRY-RUN] Cliente {ag.cliente.nome} ({ag.cliente.telefone}):\n{msg_cliente}\n'))
          enviados += 1
        else:
          r = enviar_whatsapp(ag.cliente.telefone, msg_cliente)
          if r['sucesso']:
            self.stdout.write(self.style.SUCCESS(
              f'  ✅ Enviado → {ag.cliente.nome}'))
            enviados += 1
          else:
            self.stdout.write(self.style.ERROR(
              f'  ❌ Falha → {ag.cliente.nome}: {r["resposta"]}'))
            erros += 1

      if ag.esteticista.telefone:
        if dry_run:
          self.stdout.write(self.style.SUCCESS(
            f'[DRY-RUN] Esteticista {ag.esteticista} ({ag.esteticista.telefone}):\n{msg_esteticista}\n'))
        else:
          r = enviar_whatsapp(
            ag.esteticista.telefone, msg_esteticista)
          if r['sucesso']:
            self.stdout.write(self.style.SUCCESS(
              f'  ✅ Enviado → esteticista {ag.esteticista}'))
          else:
            self.stdout.write(self.style.ERROR(
              f'  ❌ Falha → esteticista {ag.esteticista}: {r["resposta"]}'))

      Notificacao.objects.create(
        esteticista=ag.esteticista,
        agendamento=ag,
        tipo='lembrete',
        mensagem=f"{'[DRY-RUN] ' if dry_run else ''}Lembrete WhatsApp → {ag.cliente.nome} às {hora_fmt} de {data_fmt}",
      )

    self.stdout.write('\n' + '─' * 42)
    self.stdout.write(self.style.SUCCESS(f'✅ Enviados: {enviados}'))
    if erros:
      self.stdout.write(self.style.ERROR(f'❌ Erros:    {erros}'))
    self.stdout.write('─' * 42)
