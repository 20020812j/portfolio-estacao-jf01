import hashlib
import hmac
import os
import sqlite3
import uuid
from datetime import datetime
from functools import wraps

import requests
from dotenv import load_dotenv
from flask import (
    Flask, abort, flash, jsonify, redirect, render_template,
    request, session, url_for
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-change-me")
DB_PATH = os.getenv("DB_PATH", "delivery.db")
MP_API = "https://api.mercadopago.com"
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")
MP_PUBLIC_KEY = os.getenv("MP_PUBLIC_KEY", "")
MP_WEBHOOK_SECRET = os.getenv("MP_WEBHOOK_SECRET", "")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000").rstrip("/")
DELIVERY_FEE = float(os.getenv("DELIVERY_FEE", "5.00"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
RESTAURANT_PHONE = os.getenv("RESTAURANT_PHONE", "5537998389365")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        category TEXT NOT NULL,
        image TEXT,
        active INTEGER NOT NULL DEFAULT 1,
        featured INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        cpf TEXT,
        delivery_type TEXT NOT NULL,
        cep TEXT,
        street TEXT,
        number TEXT,
        neighborhood TEXT,
        complement TEXT,
        notes TEXT,
        subtotal REAL NOT NULL,
        delivery_fee REAL NOT NULL,
        total REAL NOT NULL,
        payment_status TEXT NOT NULL DEFAULT 'pending',
        order_status TEXT NOT NULL DEFAULT 'new',
        payment_id TEXT,
        payment_method TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER,
        product_name TEXT NOT NULL,
        unit_price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id)
    );
    """)
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        products = [
            ("Feijoada", "Acompanha arroz, couve, farofa e laranja.", 25.00, "Pratos do dia",
             "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=80", 1, 1),
            ("Dobradinha", "Acompanha arroz e pirão.", 25.00, "Pratos do dia",
             "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=900&q=80", 1, 1),
            ("Sopa de Galinha", "Sopa caseira com frango, legumes e tempero especial.", 20.00, "Sopas e caldos",
             "https://images.unsplash.com/photo-1547592166-23ac45744acd?auto=format&fit=crop&w=900&q=80", 1, 1),
            ("Caldinho de Feijão", "Feito com feijão carioca e temperos caseiros.", 15.00, "Sopas e caldos",
             "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=80", 1, 0),
            ("Vaca Atolada", "Mandioca cremosa com carne bem temperada.", 25.00, "Pratos do dia",
             "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=900&q=80", 1, 0),
            ("Canjica Cremosa", "Canjica doce, cremosa e feita com carinho.", 12.00, "Sobremesas",
             "https://images.unsplash.com/photo-1551024506-0bccd828d307?auto=format&fit=crop&w=900&q=80", 1, 0),
            ("Refrigerante Lata", "Coca-Cola, Guaraná ou Sprite.", 6.00, "Bebidas",
             "https://images.unsplash.com/photo-1629203851122-3726ecdf080e?auto=format&fit=crop&w=900&q=80", 1, 0),
            ("Suco Natural", "Sabores variados.", 8.00, "Bebidas",
             "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?auto=format&fit=crop&w=900&q=80", 1, 0),
        ]
        conn.executemany("""
            INSERT INTO products
            (name, description, price, category, image, active, featured)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, products)
    conn.commit()
    conn.close()


@app.template_filter("brl")
def brl(value):
    value = float(value or 0)
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def get_cart():
    return session.setdefault("cart", {})


def cart_details():
    cart = get_cart()
    if not cart:
        return [], 0.0
    ids = [int(i) for i in cart.keys()]
    placeholders = ",".join("?" for _ in ids)
    conn = db()
    rows = conn.execute(
        f"SELECT * FROM products WHERE id IN ({placeholders})", ids
    ).fetchall()
    conn.close()
    items, subtotal = [], 0.0
    for row in rows:
        qty = int(cart.get(str(row["id"]), 0))
        total = float(row["price"]) * qty
        subtotal += total
        items.append({**dict(row), "quantity": qty, "total": total})
    return sorted(items, key=lambda x: x["id"]), subtotal


@app.context_processor
def globals_for_templates():
    items, subtotal = cart_details()
    return {
        "cart_count": sum(i["quantity"] for i in items),
        "restaurant_phone": RESTAURANT_PHONE,
        "mp_public_key": MP_PUBLIC_KEY,
    }


@app.get("/")
def home():
    conn = db()
    featured = conn.execute(
        "SELECT * FROM products WHERE active=1 AND featured=1 ORDER BY id"
    ).fetchall()
    conn.close()
    return render_template("index.html", products=featured)


@app.get("/cardapio")
def menu():
    conn = db()
    products = conn.execute(
        "SELECT * FROM products WHERE active=1 ORDER BY category, id"
    ).fetchall()
    conn.close()
    categories = {}
    for p in products:
        categories.setdefault(p["category"], []).append(p)
    return render_template("menu.html", categories=categories)


@app.post("/carrinho/adicionar/<int:product_id>")
def add_cart(product_id):
    conn = db()
    product = conn.execute(
        "SELECT id FROM products WHERE id=? AND active=1", (product_id,)
    ).fetchone()
    conn.close()
    if not product:
        abort(404)
    cart = get_cart()
    key = str(product_id)
    cart[key] = int(cart.get(key, 0)) + max(1, int(request.form.get("quantity", 1)))
    session.modified = True
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "count": sum(cart.values())})
    flash("Item adicionado ao carrinho.", "success")
    return redirect(request.referrer or url_for("menu"))


@app.get("/carrinho")
def cart():
    items, subtotal = cart_details()
    return render_template("cart.html", items=items, subtotal=subtotal)


@app.post("/carrinho/atualizar")
def update_cart():
    cart = get_cart()
    for key in list(cart.keys()):
        try:
            qty = int(request.form.get(f"qty_{key}", cart[key]))
        except ValueError:
            qty = cart[key]
        if qty <= 0:
            cart.pop(key, None)
        else:
            cart[key] = min(qty, 20)
    session.modified = True
    return redirect(url_for("cart"))


@app.post("/carrinho/remover/<int:product_id>")
def remove_cart(product_id):
    get_cart().pop(str(product_id), None)
    session.modified = True
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, subtotal = cart_details()
    if not items:
        flash("Seu carrinho está vazio.", "warning")
        return redirect(url_for("menu"))

    if request.method == "POST":
        delivery_type = request.form.get("delivery_type", "delivery")
        fee = DELIVERY_FEE if delivery_type == "delivery" else 0.0
        total = subtotal + fee
        required = ["customer_name", "phone", "email"]
        if delivery_type == "delivery":
            required += ["cep", "street", "number", "neighborhood"]
        missing = [f for f in required if not request.form.get(f, "").strip()]
        if missing:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return redirect(url_for("checkout"))

        conn = db()
        cur = conn.execute("""
            INSERT INTO orders (
                customer_name, phone, email, cpf, delivery_type, cep, street,
                number, neighborhood, complement, notes, subtotal, delivery_fee,
                total, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["customer_name"].strip(),
            request.form["phone"].strip(),
            request.form["email"].strip(),
            request.form.get("cpf", "").strip(),
            delivery_type,
            request.form.get("cep", "").strip(),
            request.form.get("street", "").strip(),
            request.form.get("number", "").strip(),
            request.form.get("neighborhood", "").strip(),
            request.form.get("complement", "").strip(),
            request.form.get("notes", "").strip(),
            subtotal, fee, total, datetime.now().isoformat(timespec="seconds")
        ))
        order_id = cur.lastrowid
        conn.executemany("""
            INSERT INTO order_items
            (order_id, product_id, product_name, unit_price, quantity)
            VALUES (?, ?, ?, ?, ?)
        """, [
            (order_id, i["id"], i["name"], i["price"], i["quantity"])
            for i in items
        ])
        conn.commit()
        conn.close()
        session["checkout_order_id"] = order_id
        return redirect(url_for("payment", order_id=order_id))

    return render_template(
        "checkout.html", items=items, subtotal=subtotal, delivery_fee=DELIVERY_FEE
    )


@app.get("/pagamento/<int:order_id>")
def payment(order_id):
    if session.get("checkout_order_id") != order_id:
        abort(403)
    conn = db()
    order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    conn.close()
    if not order:
        abort(404)
    return render_template("payment.html", order=order)


@app.post("/api/process_payment/<int:order_id>")
def process_payment(order_id):
    if session.get("checkout_order_id") != order_id:
        return jsonify({"error": "Pedido inválido."}), 403
    if not MP_ACCESS_TOKEN:
        return jsonify({"error": "MP_ACCESS_TOKEN não configurado no servidor."}), 500

    conn = db()
    order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    conn.close()
    if not order:
        return jsonify({"error": "Pedido não encontrado."}), 404
    if order["payment_status"] == "approved":
        return jsonify({"status": "approved", "order_id": order_id})

    incoming = request.get_json(silent=True) or {}
    payer_in = incoming.get("payer") or {}
    payment_method_id = incoming.get("payment_method_id")
    if not payment_method_id:
        return jsonify({"error": "Forma de pagamento não informada."}), 400

    payload = {
        "transaction_amount": round(float(order["total"]), 2),
        "description": f"Pedido #{order_id} - Claudia Santos Delicias Caseiras",
        "payment_method_id": payment_method_id,
        "external_reference": str(order_id),
        "notification_url": f"{BASE_URL}/webhooks/mercadopago",
        "payer": {
            "email": order["email"],
            "first_name": order["customer_name"].split()[0],
        },
        "metadata": {"order_id": order_id},
    }

    if order["cpf"]:
        payload["payer"]["identification"] = {
            "type": "CPF",
            "number": "".join(c for c in order["cpf"] if c.isdigit())
        }
    elif payer_in.get("identification"):
        payload["payer"]["identification"] = payer_in["identification"]

    for field in ("token", "issuer_id", "installments"):
        if incoming.get(field) not in (None, ""):
            payload[field] = incoming[field]

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()),
    }
    try:
        response = requests.post(
            f"{MP_API}/v1/payments", json=payload, headers=headers, timeout=30
        )
        data = response.json()
    except requests.RequestException:
        return jsonify({"error": "Falha ao comunicar com o Mercado Pago."}), 502
    except ValueError:
        return jsonify({"error": "Resposta inválida do Mercado Pago."}), 502

    if response.status_code >= 400:
        message = data.get("message") or "Pagamento recusado."
        causes = data.get("cause") or []
        if causes and isinstance(causes, list):
            message = causes[0].get("description", message)
        return jsonify({"error": message, "details": data}), response.status_code

    status = data.get("status", "pending")
    payment_id = str(data.get("id", ""))
    conn = db()
    conn.execute("""
        UPDATE orders
        SET payment_status=?, payment_id=?, payment_method=?
        WHERE id=?
    """, (status, payment_id, payment_method_id, order_id))
    conn.commit()
    conn.close()

    result = {
        "status": status,
        "status_detail": data.get("status_detail"),
        "payment_id": payment_id,
        "order_id": order_id,
    }
    tx = ((data.get("point_of_interaction") or {}).get("transaction_data") or {})
    if payment_method_id == "pix":
        result.update({
            "qr_code": tx.get("qr_code"),
            "qr_code_base64": tx.get("qr_code_base64"),
            "ticket_url": tx.get("ticket_url"),
        })
    return jsonify(result)


def valid_webhook_signature():
    if not MP_WEBHOOK_SECRET:
        return True
    x_signature = request.headers.get("x-signature", "")
    x_request_id = request.headers.get("x-request-id", "")
    data_id = request.args.get("data.id") or request.args.get("id", "")
    parts = dict(
        p.split("=", 1) for p in x_signature.split(",") if "=" in p
    )
    ts, received = parts.get("ts"), parts.get("v1")
    if not ts or not received:
        return False
    manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
    expected = hmac.new(
        MP_WEBHOOK_SECRET.encode(),
        manifest.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, received)


@app.route("/webhooks/mercadopago", methods=["GET", "POST"])
def mercado_pago_webhook():
    if not valid_webhook_signature():
        return "", 401

    body = request.get_json(silent=True) or {}
    payment_id = (
        request.args.get("data.id")
        or request.args.get("id")
        or (body.get("data") or {}).get("id")
    )
    if not payment_id or not MP_ACCESS_TOKEN:
        return "", 200

    try:
        response = requests.get(
            f"{MP_API}/v1/payments/{payment_id}",
            headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
            timeout=20
        )
        if response.status_code != 200:
            return "", 200
        payment = response.json()
    except (requests.RequestException, ValueError):
        return "", 200

    order_id = payment.get("external_reference") or (
        payment.get("metadata") or {}
    ).get("order_id")
    if order_id:
        conn = db()
        conn.execute("""
            UPDATE orders
            SET payment_status=?, payment_id=?, payment_method=?
            WHERE id=?
        """, (
            payment.get("status", "pending"),
            str(payment.get("id", "")),
            payment.get("payment_method_id"),
            int(order_id)
        ))
        conn.commit()
        conn.close()
    return "", 200


@app.get("/pedido/<int:order_id>")
def order_status(order_id):
    conn = db()
    order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    items = conn.execute(
        "SELECT * FROM order_items WHERE order_id=?", (order_id,)
    ).fetchall()
    conn.close()
    if not order:
        abort(404)
    return render_template("order_status.html", order=order, items=items)


@app.post("/pedido/<int:order_id>/finalizar-sessao")
def finish_order(order_id):
    session.pop("cart", None)
    session.pop("checkout_order_id", None)
    return redirect(url_for("order_status", order_id=order_id))


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if hmac.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Senha incorreta.", "danger")
    return render_template("admin/login.html")


@app.get("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


@app.get("/admin")
@admin_required
def admin_dashboard():
    conn = db()
    stats = {
        "orders": conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "revenue": conn.execute(
            "SELECT COALESCE(SUM(total),0) FROM orders WHERE payment_status='approved'"
        ).fetchone()[0],
        "pending": conn.execute(
            "SELECT COUNT(*) FROM orders WHERE order_status IN ('new','preparing')"
        ).fetchone()[0],
    }
    orders = conn.execute(
        "SELECT * FROM orders ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return render_template("admin/dashboard.html", stats=stats, orders=orders)


@app.post("/admin/pedido/<int:order_id>/status")
@admin_required
def admin_order_status(order_id):
    allowed = {"new", "preparing", "delivery", "completed", "cancelled"}
    status = request.form.get("status")
    if status not in allowed:
        abort(400)
    conn = db()
    conn.execute("UPDATE orders SET order_status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/produtos", methods=["GET", "POST"])
@admin_required
def admin_products():
    conn = db()
    if request.method == "POST":
        conn.execute("""
            INSERT INTO products
            (name, description, price, category, image, active, featured)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (
            request.form["name"],
            request.form["description"],
            float(request.form["price"].replace(",", ".")),
            request.form["category"],
            request.form.get("image", ""),
            1 if request.form.get("featured") else 0,
        ))
        conn.commit()
        flash("Produto cadastrado.", "success")
    products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin/products.html", products=products)


@app.post("/admin/produtos/<int:product_id>/alternar")
@admin_required
def toggle_product(product_id):
    conn = db()
    conn.execute(
        "UPDATE products SET active = CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?",
        (product_id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("admin_products"))


@app.get("/health")
def health():
    return {"status": "ok"}


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)
