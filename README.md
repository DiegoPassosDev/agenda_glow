# Agenda Glow

Sistema web responsivo para gerenciamento de agendamentos de serviços estéticos, desenvolvido com Django.

## Funcionalidades

- ✅ Dashboard com visualização diária dos agendamentos
- ✅ Navegação entre datas (anterior/posterior)
- ✅ Criação, edição e cancelamento de agendamentos
- ✅ Cadastro e listagem de clientes
- ✅ Notificações de novos agendamentos e cancelamentos
- ✅ Lembretes automáticos via WhatsApp (Evolution API)
- ✅ Sistema de permissões (só pode editar próprios agendamentos)
- ✅ Interface mobile-first com design elegante
- ✅ Autenticação de usuários

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/DiegoPassosDev/agenda_glow
cd agenda-glow
```

### 2. Criar ambiente virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar ambiente

Copie o arquivo de exemplo de variáveis de ambiente:

```bash
cp .env.example .env
# Edite o .env com suas configurações
```

### 5. Configurar banco de dados

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Criar superusuário

```bash
python manage.py createsuperuser
```

### 7. Criar dados iniciais (Admin)

Acesse o admin em `http://localhost:8000/admin/` e:

1. Crie um objeto `Esteticista` associado ao seu usuário
2. Crie alguns `Serviços` (ex: Manicure - 30min - R$40,00)
3. Crie alguns `Clientes`

### 8. Executar servidor

```bash
python manage.py runserver
```

Acesse: `http://localhost:8000/`

## Uso

### Login
Use as credenciais do superusuário criado.

### Dashboard
- Visualize agendamentos do dia
- Navegue entre datas usando as setas
- Veja notificações no sino
- Acesse o menu lateral no ícone de hamburger

### Criar Agendamento
1. Clique em "+ Novo Agendamento"
2. Selecione cliente, serviço, data e hora
3. Adicione observações se necessário
4. Salve

### Editar/Cancelar
- Somente agendamentos criados por você podem ser editados
- Clique em "Editar" ou "Cancelar" no card do agendamento
- Outras esteticistas serão notificadas das alterações

### Lembretes Automáticos

Para enviar lembretes automaticamente, configure uma tarefa cron (Linux/Mac) ou Task Scheduler (Windows):

**Linux/Mac (crontab):**
```bash
# Executar a cada 5 minutos
*/5 * * * * cd /caminho/do/projeto && /caminho/do/venv/bin/python manage.py enviar_lembretes
```

**Windows (Task Scheduler):**
- Criar nova tarefa
- Trigger: A cada 5 minutos
- Action: Executar `C:\caminho\do\venv\Scripts\python.exe C:\caminho\do\projeto\manage.py enviar_lembretes`

## Personalização

### Cores
Edite as variáveis CSS em `templates/static/styles/base.css`:
```css
:root {
    --bg-primary: #C6E2DA;
    --color-accent: #FF6B6B;
    --color-info: #4ECDC4;
}
```

### Horários de Funcionamento
Edite em `views.py` na função `dashboard` a parte:
```python
hora_atual = 8  # Horário inicial
while hora_atual < 18:  # Horário final
```

## Tecnologias Utilizadas

- **Backend:** Django 4.2+
- **Frontend:** HTML5, CSS3, JavaScript vanilla
- **Fontes:** Merriweather (Google Fonts)
- **Database:** SQLite (padrão Django, pode ser alterado)

## Recursos Adicionais

### Adicionar mais esteticistas
1. Crie usuários no admin do Django
2. Crie um objeto `Esteticista` associado a cada usuário

### Backup do banco de dados
```bash
python manage.py dumpdata > backup.json
```

### Restaurar backup
```bash
python manage.py loaddata backup.json
```

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs do Django
2. Confirme que todas as migrações foram aplicadas
3. Verifique se o usuário tem um objeto `Esteticista` associado

## Licença

Este projeto é de uso livre para fins educacionais e comerciais.

---

Desenvolvido com ❤️ para facilitar o dia a dia das esteticistas!
