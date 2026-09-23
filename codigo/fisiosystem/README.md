# FisioSystem — Flask + PostgreSQL/SQLite

Versão reconstruída para rodar localmente e também ser publicada no Render.

## Recursos
- Login
- Administrador único
- Cadastro de fisioterapeutas
- Cadastro de pacientes
- Avaliação fisioterapêutica
- IMC automático
- EVA
- Goniometria
- Força muscular
- Evoluções por sessão
- Reavaliações
- Agenda
- Kanban
- Alta fisioterapêutica
- Relatório imprimível
- Perfil profissional com CREFITO
- Gráfico de EVA

## Rodar localmente

1. Crie um ambiente virtual:
   python -m venv .venv

2. Ative no Windows:
   .venv\Scripts\activate

3. Instale:
   pip install -r requirements.txt

4. Copie `.env.example` para `.env` e ajuste os valores.

5. Rode:
   python app.py

6. Acesse:
   http://127.0.0.1:5000

Se `DATABASE_URL` não estiver definida, o sistema usa SQLite local.

## Render

- Suba este projeto para o GitHub.
- No Render, use o `render.yaml` ou crie Web Service + PostgreSQL manualmente.
- Defina `ADMIN_PASSWORD` com uma senha forte.
- O comando de inicialização é:
  gunicorn app:app

## Segurança

Não publique usando `admin123`.
Para uso clínico real, configure backup, HTTPS, controle de acesso, política de retenção e revisão de conformidade/LGPD.
