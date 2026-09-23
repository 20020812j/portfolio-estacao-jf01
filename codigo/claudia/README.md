# Cláudia Santos Delícias Caseiras

Projeto completo em Flask para cardápio, carrinho, checkout, pagamento dentro do site com Mercado Pago, rastreamento e painel administrativo.

## 1. Preparar o projeto no Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Abra: `http://127.0.0.1:5000`

Painel: `http://127.0.0.1:5000/admin/login`

## 2. Configurar Mercado Pago

Crie uma aplicação no painel Mercado Pago Developers e copie:

- Public Key para `MP_PUBLIC_KEY`
- Access Token para `MP_ACCESS_TOKEN`
- Chave secreta do webhook para `MP_WEBHOOK_SECRET`

Use primeiro credenciais `TEST-...`.

No arquivo `.env`:

```env
SECRET_KEY=uma-chave-secreta-grande
ADMIN_PASSWORD=sua-senha-do-painel
MP_PUBLIC_KEY=TEST-...
MP_ACCESS_TOKEN=TEST-...
MP_WEBHOOK_SECRET=sua-chave-do-webhook
BASE_URL=http://127.0.0.1:5000
DELIVERY_FEE=5.00
```

Para produção, `BASE_URL` deve ser a URL pública HTTPS do Render, sem barra no final.

## 3. Webhook

No Mercado Pago, configure:

`https://SEU-SITE.onrender.com/webhooks/mercadopago`

Tópico: pagamentos.

## 4. Publicar no Render

1. Envie os arquivos para um repositório GitHub.
2. No Render, crie um Web Service pelo repositório.
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn app:app`
5. Cadastre as variáveis do `.env` no painel Environment.

Atenção: SQLite no plano gratuito pode perder dados em reinícios/deploys. Para uso real, migre para PostgreSQL ou configure um Persistent Disk.

## 5. Segurança antes de vender

- Troque `ADMIN_PASSWORD` e `SECRET_KEY`.
- Não envie `.env` ao GitHub.
- Teste Pix, cartão aprovado e cartão recusado.
- Ative e valide o webhook.
- Confira taxa de entrega, endereço, preços e política de cancelamento.
- Use credenciais de produção apenas após finalizar os testes.

## Rotas principais

- `/` página inicial
- `/cardapio`
- `/carrinho`
- `/checkout`
- `/admin/login`
- `/webhooks/mercadopago`
- `/health`
