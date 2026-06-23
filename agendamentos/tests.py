from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Cliente, Servico, Esteticista, Agendamento, Notificacao


class ClienteModelTest(TestCase):
  def setUp(self):
    self.cliente = Cliente.objects.create(
      nome="maria silva",
      telefone="(11) 99999-8888",
      email="maria@email.com",
    )

  def test_nome_upper_on_save(self):
    self.assertEqual(self.cliente.nome, "MARIA SILVA")

  def test_str(self):
    self.assertEqual(str(self.cliente), "MARIA SILVA")

  def test_ordering(self):
    Cliente.objects.create(nome="ana souza", telefone="11988887777")
    clientes = Cliente.objects.all()
    self.assertEqual(clientes[0].nome, "ANA SOUZA")
    self.assertEqual(clientes[1].nome, "MARIA SILVA")


class ServicoModelTest(TestCase):
  def setUp(self):
    self.servico = Servico.objects.create(
      nome="limpeza de pele",
      duracao_minutos=60,
      preco=120.00,
    )

  def test_nome_upper_on_save(self):
    self.assertEqual(self.servico.nome, "LIMPEZA DE PELE")

  def test_str(self):
    self.assertIn("LIMPEZA DE PELE", str(self.servico))
    self.assertIn("60", str(self.servico))

  def test_default_ativo(self):
    self.assertTrue(self.servico.ativo)

  def test_ordering(self):
    Servico.objects.create(nome="massagem", duracao_minutos=30, preco=80)
    servicos = Servico.objects.all()
    self.assertEqual(servicos[0].nome, "LIMPEZA DE PELE")
    self.assertEqual(servicos[1].nome, "MASSAGEM")


class EsteticistaModelTest(TestCase):
  def setUp(self):
    self.user = User.objects.create_user(username="esteticista1", password="teste123")
    self.esteticista = Esteticista.objects.create(
      user=self.user, telefone="11988887777"
    )

  def test_str(self):
    self.assertEqual(str(self.esteticista), "esteticista1")

  def test_str_full_name(self):
    self.user.first_name = "Ana"
    self.user.last_name = "Silva"
    self.user.save()
    self.assertEqual(str(self.esteticista), "Ana Silva")


class AgendamentoModelTest(TestCase):
  def setUp(self):
    self.user = User.objects.create_user(username="esteticista2", password="teste123")
    self.esteticista = Esteticista.objects.create(user=self.user)
    self.cliente = Cliente.objects.create(nome="joao", telefone="11988887777")
    self.servico = Servico.objects.create(
      nome="manicure", duracao_minutos=30, preco=50
    )
    self.agendamento = Agendamento.objects.create(
      esteticista=self.esteticista,
      cliente=self.cliente,
      servico=self.servico,
      data_hora=timezone.now() + timedelta(hours=2),
    )

  def test_default_status(self):
    self.assertEqual(self.agendamento.status, "agendado")

  def test_duracao_from_servico(self):
    self.assertEqual(self.agendamento.duracao_minutos, 30)

  def test_hora_fim(self):
    esperado = self.agendamento.data_hora + timedelta(minutes=30)
    self.assertEqual(self.agendamento.hora_fim, esperado)

  def test_esta_proximo(self):
    agendamento_proximo = Agendamento.objects.create(
      esteticista=self.esteticista,
      cliente=self.cliente,
      servico=self.servico,
      data_hora=timezone.now() + timedelta(minutes=5),
    )
    self.assertTrue(agendamento_proximo.esta_proximo)

  def test_nao_esta_proximo(self):
    self.assertFalse(self.agendamento.esta_proximo)

  def test_status_choices_valid(self):
    for status, _ in Agendamento.STATUS_CHOICES:
      self.agendamento.status = status
      self.agendamento.save()
      self.assertEqual(
        Agendamento.objects.get(pk=self.agendamento.pk).status, status
      )

  def test_str_contains_client_and_date(self):
    self.assertIn("JOAO", str(self.agendamento))


class NotificacaoModelTest(TestCase):
  def setUp(self):
    self.user = User.objects.create_user(username="esteticista3", password="teste123")
    self.esteticista = Esteticista.objects.create(user=self.user)
    self.notificacao = Notificacao.objects.create(
      esteticista=self.esteticista,
      tipo="lembrete",
      mensagem="Teste de notificação",
    )

  def test_default_lida(self):
    self.assertFalse(self.notificacao.lida)

  def test_str(self):
    self.assertIn("lembrete", str(self.notificacao))

  def test_ordering(self):
    Notificacao.objects.create(
      esteticista=self.esteticista, tipo="cancelamento", mensagem="outra"
    )
    notificacoes = Notificacao.objects.all()
    self.assertGreaterEqual(
      notificacoes[0].criada_em, notificacoes[1].criada_em
    )


class AgendamentoFormTest(TestCase):
  def setUp(self):
    self.user = User.objects.create_user(username="esteticista4", password="teste123")
    self.esteticista = Esteticista.objects.create(user=self.user)
    self.cliente = Cliente.objects.create(nome="carla", telefone="11988887777")
    self.servico = Servico.objects.create(
      nome="depilacao", duracao_minutos=45, preco=80
    )

  def test_form_invalido_sem_dados(self):
    from .forms import AgendamentoForm

    form = AgendamentoForm(data={}, esteticista=self.esteticista)
    self.assertFalse(form.is_valid())

  def test_form_invalido_data_passada(self):
    from .forms import AgendamentoForm

    data = (timezone.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    hora = "10:00"
    form = AgendamentoForm(
      data={
        "cliente": self.cliente.pk,
        "servico": self.servico.pk,
        "data": data,
        "hora": hora,
      },
      esteticista=self.esteticista,
    )
    self.assertFalse(form.is_valid())
    self.assertIn("não é possível", str(form.errors).lower())


class ClienteFormTest(TestCase):
  def test_form_valido(self):
    from .forms import ClienteForm

    form = ClienteForm(
      data={"nome": "Pedro", "telefone": "11988887777", "email": "pedro@email.com"}
    )
    self.assertTrue(form.is_valid())

  def test_form_invalido_sem_nome(self):
    from .forms import ClienteForm

    form = ClienteForm(data={"telefone": "11988887777"})
    self.assertFalse(form.is_valid())

  def test_form_invalido_sem_telefone(self):
    from .forms import ClienteForm

    form = ClienteForm(data={"nome": "Pedro"})
    self.assertFalse(form.is_valid())
