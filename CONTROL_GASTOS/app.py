import os
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, g

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "solo-desarrollo-cambiar-esta-clave")
DB = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "gastos.db"))
USER = os.environ.get("ADMIN_USER", "admin")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "123")

CSS = """<style>
*{box-sizing:border-box}body{margin:0;background:#f5f6fa;color:#182234;font:16px Arial,sans-serif}
header{background:#8b1538;color:white;padding:20px 7%;display:flex;justify-content:space-between;align-items:center}
header a{color:white;text-decoration:none;margin-left:18px}main{max-width:1100px;margin:35px auto;padding:0 20px}
.card{background:white;border:1px solid #e2e5ed;border-radius:15px;padding:25px;margin-bottom:20px;box-shadow:0 4px 18px #1822340a}
h1{margin:0 0 12px}h2{font-size:20px}label{display:block;font-weight:bold;margin:12px 0 6px}
input{width:100%;padding:12px;border:1px solid #cbd2df;border-radius:8px;font:inherit}
button,.btn{display:inline-block;background:#a81d43;color:white;border:0;border-radius:8px;padding:12px 17px;cursor:pointer;text-decoration:none;font-weight:bold}
.secondary{background:#263146}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
table{width:100%;border-collapse:collapse}th,td{padding:12px;text-align:left;border-bottom:1px solid #e8eaf0}
.tablewrap{overflow-x:auto}.muted{color:#697386}.metric{font-size:30px;font-weight:bold;color:#a81d43}
.msg{padding:12px;background:#fff0d7;border-radius:8px;margin:10px 0}
@media print{header,form,.no-print{display:none!important}body{background:white}.card{box-shadow:none}}
</style>"""
BASE = """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Control de Gastos</title>""" + CSS + """</head><body>
<header><strong>CONTROL DE GASTOS</strong><nav>{% if session.get('logged_in') %}
<a href="{{ url_for('index') }}">Registrar gastos</a><a href="{{ url_for('reporte') }}">Reportes</a>
<a href="{{ url_for('logout') }}">Salir</a>{% endif %}</nav></header>
<main>{% for message in get_flashed_messages() %}<div class="msg">{{ message }}</div>{% endfor %}
{{ body|safe }}</main></body></html>"""

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    conn = g.pop("db", None)
    if conn is not None: conn.close()

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB)), exist_ok=True)
    with sqlite3.connect(DB) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            monto_centavos INTEGER NOT NULL CHECK(monto_centavos > 0),
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

def page(template, **kwargs):
    body = render_template_string(template, **kwargs)
    return render_template_string(BASE, body=body)

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"): return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("usuario") == USER and request.form.get("clave") == PASSWORD:
            session.clear()
            session["logged_in"] = True
            return redirect(url_for("index"))
        flash("Usuario o contraseña incorrectos.")
    return page("""<section class="card" style="max-width:450px;margin:70px auto">
    <h1>Acceso administrativo</h1><p class="muted">Ingresa para administrar tus gastos.</p>
    <form method="post"><label>Usuario</label><input name="usuario" required autocomplete="username">
    <label>Contraseña</label><input type="password" name="clave" required autocomplete="current-password">
    <p><button>Iniciar sesión</button></p></form></section>""")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        fecha = request.form.get("fecha", "")
        descripcion = request.form.get("descripcion", "").strip()
        monto = request.form.get("monto", "").strip()
        try:
            date.fromisoformat(fecha)
            if not descripcion or len(descripcion) > 250: raise ValueError()
            value = Decimal(monto)
            cents = value * 100
            if not value.is_finite() or cents != cents.to_integral_value() or cents <= 0 or cents > 999999999999: raise ValueError()
            db().execute("INSERT INTO gastos(fecha,descripcion,monto_centavos) VALUES(?,?,?)", (fecha, descripcion, int(cents)))
            db().commit()
            flash("Gasto registrado correctamente.")
            return redirect(url_for("index"))
        except (ValueError, InvalidOperation):
            flash("Verifica la fecha, descripción y monto (positivo, máximo dos decimales).")
    rows = db().execute("SELECT * FROM gastos ORDER BY fecha DESC,id DESC LIMIT 30").fetchall()
    total = db().execute("SELECT COALESCE(SUM(monto_centavos),0) FROM gastos").fetchone()[0]
    return page("""<h1>Registro de gastos</h1><p class="muted">Guarda tus gastos y consulta tus movimientos.</p>
    <div class="grid"><section class="card"><h2>Nuevo gasto</h2>
    <form method="post"><label>Fecha</label><input type="date" name="fecha" value="{{ hoy }}" required>
    <label>Descripción</label><input name="descripcion" maxlength="250" placeholder="Ej.: Compra de materiales" required>
    <label>Monto (S/)</label><input type="number" name="monto" min="0.01" step="0.01" required>
    <p><button>Registrar gasto</button></p></form></section>
    <section class="card"><h2>Total de gastos</h2><div class="metric">S/ {{ '%.2f'|format(total/100) }}</div>
    <p class="muted">Suma histórica de los registros.</p><a class="btn secondary" href="{{ url_for('reporte') }}">Ver reportes</a></section></div>
    <section class="card"><h2>Últimos gastos</h2><div class="tablewrap"><table><thead><tr><th>Fecha</th><th>Descripción</th><th>Monto</th></tr></thead><tbody>
    {% for r in rows %}<tr><td>{{ r['fecha'] }}</td><td>{{ r['descripcion'] }}</td><td>S/ {{ '%.2f'|format(r['monto_centavos']/100) }}</td></tr>
    {% else %}<tr><td colspan="3">Aún no hay gastos registrados.</td></tr>{% endfor %}
    </tbody></table></div></section>""", hoy=date.today().isoformat(), rows=rows, total=total)

@app.route("/reporte")
@login_required
def reporte():
    desde = request.args.get("desde", "")
    hasta = request.args.get("hasta", "")
    for value in (desde, hasta):
        if value:
            try: date.fromisoformat(value)
            except ValueError:
                flash("El rango de fechas no es válido.")
                return redirect(url_for("reporte"))
    if desde and hasta and desde > hasta:
        flash("La fecha inicial no puede ser posterior a la final.")
        return redirect(url_for("reporte"))
    sql = "SELECT * FROM gastos WHERE 1=1"
    params = []
    if desde: sql += " AND fecha >= ?"; params.append(desde)
    if hasta: sql += " AND fecha <= ?"; params.append(hasta)
    rows = db().execute(sql + " ORDER BY fecha DESC,id DESC", params).fetchall()
    total = sum(r["monto_centavos"] for r in rows)
    return page("""<h1>Reporte de gastos</h1><p class="muted">Filtra por fechas y guarda el reporte como PDF desde el navegador.</p>
    <section class="card"><form method="get"><div class="grid">
    <div><label>Desde</label><input type="date" name="desde" value="{{ desde }}"></div>
    <div><label>Hasta</label><input type="date" name="hasta" value="{{ hasta }}"></div></div>
    <p><button>Generar reporte</button> <button type="button" class="secondary" onclick="window.print()">Imprimir / Guardar PDF</button></p></form></section>
    <div class="grid"><section class="card"><h2>Total del período</h2><div class="metric">S/ {{ '%.2f'|format(total/100) }}</div></section>
    <section class="card"><h2>Gastos registrados</h2><div class="metric">{{ rows|length }}</div></section></div>
    <section class="card"><h2>Detalle de gastos</h2><div class="tablewrap"><table>
    <thead><tr><th>Fecha</th><th>Descripción</th><th>Monto</th></tr></thead><tbody>
    {% for r in rows %}<tr><td>{{ r['fecha'] }}</td><td>{{ r['descripcion'] }}</td><td>S/ {{ '%.2f'|format(r['monto_centavos']/100) }}</td></tr>
    {% else %}<tr><td colspan="3">No hay gastos para el período seleccionado.</td></tr>{% endfor %}
    </tbody></table></div></section>""", desde=desde, hasta=hasta, rows=rows, total=total)

init_db()
if __name__ == "__main__":
    app.run(debug=True)
