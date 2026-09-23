\
import os
from datetime import datetime, date
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")

database_url = os.getenv("DATABASE_URL", "sqlite:///fisiosystem.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Faça login para continuar."
login_manager.login_message_category = "warning"


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(30), nullable=False, default="fisioterapeuta")
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    crefito = db.Column(db.String(60))
    especialidade = db.Column(db.String(120))
    telefone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_admin(self):
        return self.perfil == "admin"


class Paciente(db.Model):
    __tablename__ = "pacientes"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, index=True)
    cpf = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)
    telefone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    profissao = db.Column(db.String(120))
    endereco = db.Column(db.String(255))
    status = db.Column(db.String(40), nullable=False, default="avaliacao")
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


class Avaliacao(db.Model):
    __tablename__ = "avaliacoes"
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False, index=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    data_avaliacao = db.Column(db.Date, nullable=False, default=date.today)
    queixa_principal = db.Column(db.Text)
    historia_doenca = db.Column(db.Text)
    antecedentes = db.Column(db.Text)
    medicamentos = db.Column(db.Text)
    diagnostico_medico = db.Column(db.Text)
    diagnostico_fisioterapeutico = db.Column(db.Text)
    objetivos = db.Column(db.Text)
    conduta = db.Column(db.Text)
    peso = db.Column(db.Float)
    altura = db.Column(db.Float)
    imc = db.Column(db.Float)
    eva = db.Column(db.Integer)
    goniometria = db.Column(db.Text)
    forca_muscular = db.Column(db.Text)
    observacoes = db.Column(db.Text)


class Evolucao(db.Model):
    __tablename__ = "evolucoes"
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False, index=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    data_sessao = db.Column(db.Date, nullable=False, default=date.today)
    numero_sessao = db.Column(db.Integer)
    eva_antes = db.Column(db.Integer)
    eva_depois = db.Column(db.Integer)
    procedimentos = db.Column(db.Text)
    evolucao = db.Column(db.Text)
    proxima_conduta = db.Column(db.Text)


class Reavaliacao(db.Model):
    __tablename__ = "reavaliacoes"
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False, index=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    data_reavaliacao = db.Column(db.Date, nullable=False, default=date.today)
    peso = db.Column(db.Float)
    altura = db.Column(db.Float)
    imc = db.Column(db.Float)
    eva = db.Column(db.Integer)
    goniometria = db.Column(db.Text)
    forca_muscular = db.Column(db.Text)
    observacoes = db.Column(db.Text)


class Agendamento(db.Model):
    __tablename__ = "agendamentos"
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    inicio = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="agendado")
    observacoes = db.Column(db.Text)


class Alta(db.Model):
    __tablename__ = "altas"
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False, unique=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    data_alta = db.Column(db.Date, nullable=False, default=date.today)
    motivo = db.Column(db.Text)
    condicao_final = db.Column(db.Text)
    objetivos_alcancados = db.Column(db.Text)
    recomendacoes = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def calcular_imc(peso, altura):
    if peso and altura and altura > 0:
        return round(peso / (altura * altura), 2)
    return None


def garantir_admin():
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin = Usuario.query.filter_by(perfil="admin").first()
    if not admin:
        admin = Usuario(
            nome="Administrador",
            username=admin_username,
            perfil="admin",
            ativo=True,
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()


@app.before_request
def ensure_db():
    if not getattr(app, "_db_ready", False):
        db.create_all()
        garantir_admin()
        app._db_ready = True


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        senha = request.form.get("senha", "")
        usuario = Usuario.query.filter_by(username=username).first()
        if usuario and usuario.ativo and usuario.check_password(senha):
            login_user(usuario)
            return redirect(url_for("dashboard"))
        flash("Usuário ou senha inválidos.", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    hoje = date.today()
    total_pacientes = Paciente.query.count()
    ativos = Paciente.query.filter(Paciente.status != "alta").count()
    sessoes = Evolucao.query.count()

    inicio_mes = hoje.replace(day=1)
    altas_mes = Alta.query.filter(Alta.data_alta >= inicio_mes).count()

    agenda_hoje = Agendamento.query.filter(
        db.func.date(Agendamento.inicio) == hoje
    ).order_by(Agendamento.inicio).all()
    pacientes_agenda = {
        p.id: p.nome
        for p in Paciente.query.filter(Paciente.id.in_([a.paciente_id for a in agenda_hoje])).all()
    }

    status_labels = {"avaliacao": "Avaliação", "tratamento": "Tratamento", "reavaliacao": "Reavaliação", "alta": "Alta"}
    status_counts = [Paciente.query.filter_by(status=s).count() for s in status_labels]

    meses_labels = []
    meses_valores = []
    for i in range(5, -1, -1):
        ano = hoje.year
        mes = hoje.month - i
        while mes <= 0:
            mes += 12
            ano -= 1
        primeiro_dia = date(ano, mes, 1)
        ultimo_dia = date(ano + (1 if mes == 12 else 0), 1 if mes == 12 else mes + 1, 1)
        qtd = Evolucao.query.filter(Evolucao.data_sessao >= primeiro_dia, Evolucao.data_sessao < ultimo_dia).count()
        meses_labels.append(primeiro_dia.strftime("%b/%y"))
        meses_valores.append(qtd)

    return render_template(
        "dashboard.html",
        total_pacientes=total_pacientes,
        ativos=ativos,
        sessoes=sessoes,
        altas_mes=altas_mes,
        agenda_hoje=agenda_hoje,
        pacientes_agenda=pacientes_agenda,
        status_labels=list(status_labels.values()),
        status_counts=status_counts,
        meses_labels=meses_labels,
        meses_valores=meses_valores,
    )


@app.route("/pacientes")
@login_required
def pacientes():
    q = request.args.get("q", "").strip()
    consulta = Paciente.query
    if q:
        consulta = consulta.filter(Paciente.nome.ilike(f"%{q}%"))
    lista = consulta.order_by(Paciente.nome).all()
    return render_template("pacientes.html", pacientes=lista, q=q)


@app.route("/pacientes/novo", methods=["GET", "POST"])
@login_required
def novo_paciente():
    if request.method == "POST":
        paciente = Paciente(
            nome=request.form["nome"].strip(),
            cpf=request.form.get("cpf"),
            data_nascimento=parse_date(request.form.get("data_nascimento")),
            telefone=request.form.get("telefone"),
            email=request.form.get("email"),
            profissao=request.form.get("profissao"),
            endereco=request.form.get("endereco"),
        )
        db.session.add(paciente)
        db.session.commit()
        flash("Paciente cadastrado.", "success")
        return redirect(url_for("ficha", paciente_id=paciente.id))
    return render_template("paciente_form.html")


@app.route("/pacientes/<int:paciente_id>")
@login_required
def ficha(paciente_id):
    paciente = db.get_or_404(Paciente, paciente_id)
    avaliacoes = Avaliacao.query.filter_by(paciente_id=paciente_id).order_by(Avaliacao.data_avaliacao.desc()).all()
    evolucoes = Evolucao.query.filter_by(paciente_id=paciente_id).order_by(Evolucao.data_sessao.desc(), Evolucao.id.desc()).all()
    reavaliacoes = Reavaliacao.query.filter_by(paciente_id=paciente_id).order_by(Reavaliacao.data_reavaliacao.desc()).all()
    alta = Alta.query.filter_by(paciente_id=paciente_id).first()

    chart_labels = [e.data_sessao.strftime("%d/%m") for e in reversed(evolucoes) if e.eva_depois is not None]
    chart_values = [e.eva_depois for e in reversed(evolucoes) if e.eva_depois is not None]

    return render_template(
        "ficha.html",
        paciente=paciente,
        avaliacoes=avaliacoes,
        evolucoes=evolucoes,
        reavaliacoes=reavaliacoes,
        alta=alta,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


@app.route("/pacientes/<int:paciente_id>/avaliacao", methods=["GET", "POST"])
@login_required
def nova_avaliacao(paciente_id):
    paciente = db.get_or_404(Paciente, paciente_id)
    if request.method == "POST":
        peso = float(request.form["peso"]) if request.form.get("peso") else None
        altura = float(request.form["altura"]) if request.form.get("altura") else None
        avaliacao = Avaliacao(
            paciente_id=paciente.id,
            profissional_id=current_user.id,
            data_avaliacao=parse_date(request.form.get("data_avaliacao")) or date.today(),
            queixa_principal=request.form.get("queixa_principal"),
            historia_doenca=request.form.get("historia_doenca"),
            antecedentes=request.form.get("antecedentes"),
            medicamentos=request.form.get("medicamentos"),
            diagnostico_medico=request.form.get("diagnostico_medico"),
            diagnostico_fisioterapeutico=request.form.get("diagnostico_fisioterapeutico"),
            objetivos=request.form.get("objetivos"),
            conduta=request.form.get("conduta"),
            peso=peso,
            altura=altura,
            imc=calcular_imc(peso, altura),
            eva=int(request.form["eva"]) if request.form.get("eva") else None,
            goniometria=request.form.get("goniometria"),
            forca_muscular=request.form.get("forca_muscular"),
            observacoes=request.form.get("observacoes"),
        )
        paciente.status = "tratamento"
        db.session.add(avaliacao)
        db.session.commit()
        flash("Avaliação registrada.", "success")
        return redirect(url_for("ficha", paciente_id=paciente.id))
    return render_template("avaliacao_form.html", paciente=paciente, titulo="Nova avaliação")


@app.route("/pacientes/<int:paciente_id>/evolucao", methods=["GET", "POST"])
@login_required
def nova_evolucao(paciente_id):
    paciente = db.get_or_404(Paciente, paciente_id)
    if request.method == "POST":
        numero = Evolucao.query.filter_by(paciente_id=paciente.id).count() + 1
        evolucao = Evolucao(
            paciente_id=paciente.id,
            profissional_id=current_user.id,
            data_sessao=parse_date(request.form.get("data_sessao")) or date.today(),
            numero_sessao=numero,
            eva_antes=int(request.form["eva_antes"]) if request.form.get("eva_antes") else None,
            eva_depois=int(request.form["eva_depois"]) if request.form.get("eva_depois") else None,
            procedimentos=request.form.get("procedimentos"),
            evolucao=request.form.get("evolucao"),
            proxima_conduta=request.form.get("proxima_conduta"),
        )
        db.session.add(evolucao)
        db.session.commit()
        flash("Evolução registrada.", "success")
        return redirect(url_for("ficha", paciente_id=paciente.id))
    return render_template("evolucao_form.html", paciente=paciente)


@app.route("/pacientes/<int:paciente_id>/reavaliacao", methods=["GET", "POST"])
@login_required
def nova_reavaliacao(paciente_id):
    paciente = db.get_or_404(Paciente, paciente_id)
    if request.method == "POST":
        peso = float(request.form["peso"]) if request.form.get("peso") else None
        altura = float(request.form["altura"]) if request.form.get("altura") else None
        item = Reavaliacao(
            paciente_id=paciente.id,
            profissional_id=current_user.id,
            data_reavaliacao=parse_date(request.form.get("data_reavaliacao")) or date.today(),
            peso=peso,
            altura=altura,
            imc=calcular_imc(peso, altura),
            eva=int(request.form["eva"]) if request.form.get("eva") else None,
            goniometria=request.form.get("goniometria"),
            forca_muscular=request.form.get("forca_muscular"),
            observacoes=request.form.get("observacoes"),
        )
        paciente.status = "reavaliacao"
        db.session.add(item)
        db.session.commit()
        flash("Reavaliação registrada.", "success")
        return redirect(url_for("ficha", paciente_id=paciente.id))
    return render_template("reavaliacao_form.html", paciente=paciente)


@app.route("/kanban")
@login_required
def kanban():
    grupos = {
        "avaliacao": Paciente.query.filter_by(status="avaliacao").order_by(Paciente.nome).all(),
        "tratamento": Paciente.query.filter_by(status="tratamento").order_by(Paciente.nome).all(),
        "reavaliacao": Paciente.query.filter_by(status="reavaliacao").order_by(Paciente.nome).all(),
        "alta": Paciente.query.filter_by(status="alta").order_by(Paciente.nome).all(),
    }
    return render_template("kanban.html", grupos=grupos)


@app.route("/pacientes/<int:paciente_id>/status", methods=["POST"])
@login_required
def atualizar_status(paciente_id):
    paciente = db.get_or_404(Paciente, paciente_id)
    status = request.form.get("status")
    if status not in {"avaliacao", "tratamento", "reavaliacao", "alta"}:
        abort(400)
    paciente.status = status
    db.session.commit()
    return redirect(url_for("kanban"))


@app.route("/agenda", methods=["GET", "POST"])
@login_required
def agenda():
    if request.method == "POST":
        paciente_id = int(request.form["paciente_id"])
        inicio = datetime.strptime(request.form["inicio"], "%Y-%m-%dT%H:%M")
        item = Agendamento(
            paciente_id=paciente_id,
            profissional_id=current_user.id,
            inicio=inicio,
            status="agendado",
            observacoes=request.form.get("observacoes"),
        )
        db.session.add(item)
        db.session.commit()
        flash("Atendimento agendado.", "success")
        return redirect(url_for("agenda"))
    itens = Agendamento.query.order_by(Agendamento.inicio.asc()).all()
    pacientes_lista = Paciente.query.filter(Paciente.status != "alta").order_by(Paciente.nome).all()
    pacientes_map = {p.id: p for p in Paciente.query.all()}
    return render_template("agenda.html", itens=itens, pacientes=pacientes_lista, pacientes_map=pacientes_map)


@app.route("/pacientes/<int:paciente_id>/alta", methods=["GET", "POST"])
@login_required
def registrar_alta(paciente_id):
    paciente = db.get_or_404(Paciente, paciente_id)
    existente = Alta.query.filter_by(paciente_id=paciente.id).first()
    if request.method == "POST":
        if existente:
            item = existente
        else:
            item = Alta(paciente_id=paciente.id, profissional_id=current_user.id)
            db.session.add(item)
        item.data_alta = parse_date(request.form.get("data_alta")) or date.today()
        item.motivo = request.form.get("motivo")
        item.condicao_final = request.form.get("condicao_final")
        item.objetivos_alcancados = request.form.get("objetivos_alcancados")
        item.recomendacoes = request.form.get("recomendacoes")
        paciente.status = "alta"
        db.session.commit()
        flash("Alta registrada.", "success")
        return redirect(url_for("ficha", paciente_id=paciente.id))
    return render_template("alta_form.html", paciente=paciente, alta=existente)


def montar_linha_do_tempo_eva(avaliacoes, evolucoes, reavaliacoes):
    """Junta o EVA de avaliações, evoluções (antes/depois) e reavaliações
    numa única linha do tempo ordenada por data, para o gráfico de evolução."""
    pontos = []
    for a in avaliacoes:
        if a.eva is not None:
            pontos.append((a.data_avaliacao, a.eva, "Avaliação"))
    for e in evolucoes:
        if e.eva_antes is not None:
            pontos.append((e.data_sessao, e.eva_antes, f"Sessão {e.numero_sessao or ''} (antes)"))
        if e.eva_depois is not None:
            pontos.append((e.data_sessao, e.eva_depois, f"Sessão {e.numero_sessao or ''} (depois)"))
    for r in reavaliacoes:
        if r.eva is not None:
            pontos.append((r.data_reavaliacao, r.eva, "Reavaliação"))
    pontos.sort(key=lambda p: p[0])
    return pontos


def montar_comparacao(avaliacoes, evolucoes, reavaliacoes):
    """Monta os dados de comparação lado a lado: primeira avaliação vs. registro mais recente."""
    primeira = avaliacoes[0] if avaliacoes else None

    candidatos = []
    if evolucoes:
        ultima_evolucao = evolucoes[-1]
        candidatos.append((
            ultima_evolucao.data_sessao,
            {
                "origem": f"Sessão {ultima_evolucao.numero_sessao or '-'}",
                "eva": ultima_evolucao.eva_depois,
                "imc": None,
                "goniometria": None,
                "forca_muscular": None,
            },
        ))
    if reavaliacoes:
        ultima_reavaliacao = reavaliacoes[-1]
        candidatos.append((
            ultima_reavaliacao.data_reavaliacao,
            {
                "origem": "Reavaliação",
                "eva": ultima_reavaliacao.eva,
                "imc": ultima_reavaliacao.imc,
                "goniometria": ultima_reavaliacao.goniometria,
                "forca_muscular": ultima_reavaliacao.forca_muscular,
            },
        ))

    ultimo = None
    ultimo_data = None
    if candidatos:
        ultimo_data, ultimo = max(candidatos, key=lambda c: c[0])

    return {
        "primeira": primeira,
        "ultimo": ultimo,
        "ultimo_data": ultimo_data,
    }


@app.route("/pacientes/<int:paciente_id>/relatorio")
@login_required
def relatorio(paciente_id):
    paciente = db.get_or_404(Paciente, paciente_id)
    avaliacoes = Avaliacao.query.filter_by(paciente_id=paciente_id).order_by(Avaliacao.data_avaliacao).all()
    evolucoes = Evolucao.query.filter_by(paciente_id=paciente_id).order_by(Evolucao.data_sessao).all()
    reavaliacoes = Reavaliacao.query.filter_by(paciente_id=paciente_id).order_by(Reavaliacao.data_reavaliacao).all()
    alta = Alta.query.filter_by(paciente_id=paciente_id).first()

    linha_do_tempo = montar_linha_do_tempo_eva(avaliacoes, evolucoes, reavaliacoes)
    eva_labels = [p[0].strftime("%d/%m/%Y") for p in linha_do_tempo]
    eva_valores = [p[1] for p in linha_do_tempo]
    comparacao = montar_comparacao(avaliacoes, evolucoes, reavaliacoes)

    return render_template(
        "relatorio.html",
        paciente=paciente,
        avaliacoes=avaliacoes,
        evolucoes=evolucoes,
        reavaliacoes=reavaliacoes,
        alta=alta,
        eva_labels=eva_labels,
        eva_valores=eva_valores,
        comparacao=comparacao,
    )


@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    if request.method == "POST":
        current_user.nome = request.form["nome"].strip()
        current_user.crefito = request.form.get("crefito")
        current_user.especialidade = request.form.get("especialidade")
        current_user.telefone = request.form.get("telefone")
        current_user.email = request.form.get("email")
        nova_senha = request.form.get("nova_senha")
        if nova_senha:
            current_user.set_password(nova_senha)
        db.session.commit()
        flash("Perfil atualizado.", "success")
        return redirect(url_for("perfil"))
    return render_template("perfil.html")


@app.route("/usuarios")
@admin_required
def usuarios():
    lista = Usuario.query.order_by(Usuario.nome).all()
    return render_template("usuarios.html", usuarios=lista)


@app.route("/usuarios/novo", methods=["GET", "POST"])
@admin_required
def novo_usuario():
    if request.method == "POST":
        username = request.form["username"].strip()
        if Usuario.query.filter_by(username=username).first():
            flash("Esse usuário já existe.", "danger")
            return redirect(url_for("novo_usuario"))
        usuario = Usuario(
            nome=request.form["nome"].strip(),
            username=username,
            perfil="fisioterapeuta",
            ativo=True,
            crefito=request.form.get("crefito"),
            especialidade=request.form.get("especialidade"),
        )
        usuario.set_password(request.form["senha"])
        db.session.add(usuario)
        db.session.commit()
        flash("Fisioterapeuta criado.", "success")
        return redirect(url_for("usuarios"))
    return render_template("usuario_form.html")


@app.route("/usuarios/<int:usuario_id>/toggle", methods=["POST"])
@admin_required
def toggle_usuario(usuario_id):
    usuario = db.get_or_404(Usuario, usuario_id)
    if usuario.is_admin:
        flash("A conta administrativa principal não pode ser desativada.", "warning")
        return redirect(url_for("usuarios"))
    usuario.ativo = not usuario.ativo
    db.session.commit()
    return redirect(url_for("usuarios"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        garantir_admin()
    app.run(debug=True)
