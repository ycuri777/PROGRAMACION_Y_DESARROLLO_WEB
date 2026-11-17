import os, sqlite3
from datetime import date, datetime
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, abort

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion")
DB = os.environ.get("DATABASE_PATH", "tienda.db")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "123")

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS products(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT NOT NULL,
          description TEXT DEFAULT '', price REAL NOT NULL CHECK(price>=0), stock INTEGER NOT NULL DEFAULT 0 CHECK(stock>=0),
          icon TEXT DEFAULT '💻', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS sales(
          id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, product_name TEXT NOT NULL,
          quantity INTEGER NOT NULL, unit_price REAL NOT NULL, total REAL NOT NULL,
          customer TEXT DEFAULT 'Venta mostrador', sale_date TEXT NOT NULL,
          FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL);
        """)
        count = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            sample = [
              ("Teclado mecánico RGB","Periféricos","Switches táctiles, iluminación RGB y conexión USB.",189,12,"⌨️"),
              ("Mouse gamer 7200 DPI","Periféricos","Sensor óptico de alta precisión y 6 botones.",79,20,"🖱️"),
              ("Monitor IPS 24 pulgadas","Monitores","Panel Full HD de 100 Hz.",599,7,"🖥️"),
              ("Memoria RAM DDR4 16 GB","Componentes","Módulo de memoria para PC de escritorio.",159,15,"🧩"),
              ("SSD NVMe 1 TB","Almacenamiento","Unidad de estado sólido de alta velocidad.",299,9,"💾"),
              ("Audífonos gaming 7.1","Audio","Micrófono integrado y sonido envolvente.",139,11,"🎧"),
              ("Tarjeta gráfica RTX","Componentes","Gráficos dedicados para gaming y creación.",1899,3,"🎮"),
              ("Fuente 650W certificada","Componentes","Fuente de poder eficiente para PC.",269,6,"⚡")]
            con.executemany("INSERT INTO products(name,category,description,price,stock,icon) VALUES(?,?,?,?,?,?)", sample)

BASE = """
<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} | UPRIT Tech Store</title><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root{--red:#a51e3b;--red2:#c12b4b;--ink:#171923;--muted:#737887;--line:#ececf1;--paper:#f7f7fa;--white:#fff}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:'DM Sans',sans-serif}a{text-decoration:none;color:inherit}.top{background:#81172f;color:#fff;text-align:center;padding:8px;font-size:12px;letter-spacing:.7px}.nav{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:4}.navin{max-width:1180px;margin:auto;padding:14px 24px;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{display:flex;align-items:center;gap:11px}.brand img{width:44px;height:48px}.brand b{font:700 17px 'Space Grotesk';color:var(--red);line-height:1.05;display:block}.brand small{font-size:10px;color:#777;letter-spacing:1.6px}.links{display:flex;gap:23px;align-items:center;font-size:13px;font-weight:700}.links a:hover{color:var(--red)}.btn{display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:9px;padding:11px 16px;background:var(--red);color:#fff;font-weight:800;font-size:13px;cursor:pointer}.btn:hover{background:#81172f}.btn.light{background:#f7e9ed;color:var(--red)}.btn.dark{background:var(--ink)}.wrap{max-width:1180px;margin:auto;padding:30px 24px}.hero{background:linear-gradient(115deg,#78152c 0%,#a51e3b 53%,#d34b68 100%);border-radius:22px;color:white;padding:52px 54px;display:grid;grid-template-columns:1.3fr .7fr;align-items:center;overflow:hidden;position:relative;min-height:340px}.hero:after{content:'UPRIT';position:absolute;font:700 170px 'Space Grotesk';right:-12px;bottom:-65px;color:#ffffff0d}.eyebrow{font-size:11px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;color:#ffd5df}.hero h1{font:700 clamp(35px,5vw,58px)/1.02 'Space Grotesk';margin:15px 0}.hero p{color:#f8dce3;max-width:510px;line-height:1.7}.heroart{font-size:116px;text-align:center;filter:drop-shadow(0 18px 14px #4b071c66);transform:rotate(-8deg)}.sectionhead{display:flex;justify-content:space-between;align-items:end;margin:34px 0 18px}.sectionhead h2{font:700 27px 'Space Grotesk';margin:0}.muted{color:var(--muted);font-size:13px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:17px}.product,.panel,.stat{background:#fff;border:1px solid var(--line);border-radius:15px}.product{padding:17px;transition:.2s}.product:hover{transform:translateY(-4px);box-shadow:0 12px 30px #17192312}.picon{height:145px;background:linear-gradient(135deg,#f8edf0,#f2f2f6);border-radius:11px;display:grid;place-items:center;font-size:67px}.tag{font-size:10px;color:var(--red);font-weight:800;text-transform:uppercase;letter-spacing:1px;margin-top:15px}.product h3{font:700 16px 'Space Grotesk';margin:7px 0}.product p{font-size:12px;color:var(--muted);line-height:1.5;min-height:36px}.price{font:700 22px 'Space Grotesk';color:var(--red)}.stock{font-size:11px;color:#777;margin:8px 0 12px}.product form{display:flex;gap:7px}.product input{width:55px;padding:9px;border:1px solid var(--line);border-radius:8px}.footer{margin-top:55px;background:#171923;color:#c8cad2;padding:35px 24px;text-align:center;font-size:12px}.footer b{color:white}.flash{padding:12px 15px;border-radius:9px;background:#f9e8ed;color:#8c1834;margin:0 0 15px;font-size:13px}.pagehead{margin:0 0 22px}.pagehead h1{font:700 32px 'Space Grotesk';margin:0 0 5px}.panel{padding:22px;margin-bottom:18px}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-bottom:20px}.stat{padding:20px}.stat small{color:var(--muted);font-weight:700}.stat strong{display:block;font:700 27px 'Space Grotesk';margin-top:8px}.formgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.field label{display:block;font-size:12px;font-weight:800;margin-bottom:6px}.field input,.field select,.field textarea{width:100%;padding:12px;border:1px solid #dedfe6;border-radius:9px;font:inherit;background:white}.field textarea{min-height:78px}.field.full{grid-column:1/-1}table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:13px 10px;border-bottom:1px solid var(--line)}th{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#777}.actions{display:flex;gap:7px}.inline{display:inline}.login{max-width:420px;margin:55px auto}.login .panel{padding:30px}.login h1{font:700 29px 'Space Grotesk'}.empty{text-align:center;padding:35px;color:var(--muted)}.cover{background:#fff;border-bottom:1px solid var(--line);padding:24px}.coverin{max-width:1180px;margin:auto;display:flex;justify-content:space-between;align-items:center}.cover h1{font:700 28px 'Space Grotesk';color:var(--red);margin:0}.cover p{font-size:12px;color:#777;margin:4px 0}.adminnav{display:flex;gap:9px;flex-wrap:wrap;margin:0 0 22px}.adminnav a{padding:9px 13px;background:#fff;border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:800}.adminnav a.active{background:#f8e9ed;color:var(--red);border-color:#f0cbd4}
@media(max-width:850px){.grid{grid-template-columns:repeat(2,1fr)}.hero{grid-template-columns:1fr;padding:35px}.heroart{display:none}.links{gap:10px;font-size:11px}.stats{grid-template-columns:1fr}.wrap{padding:22px 16px}}@media(max-width:520px){.grid{grid-template-columns:1fr}.links a:nth-child(2){display:none}.navin{padding:12px}.formgrid{grid-template-columns:1fr}.field.full{grid-column:auto}.hero{padding:28px}.hero h1{font-size:38px}.coverin{align-items:flex-start;gap:10px;flex-direction:column}}
</style></head><body><div class="top">TECNOLOGÍA QUE IMPULSA TUS IDEAS · ENVÍOS A TODO EL PERÚ</div>
<nav class="nav"><div class="navin"><a class="brand" href="{{ url_for('home') }}"><img src="{{ url_for('static',filename='uprit-mark.svg') }}"><span><b>UPRIT TECH STORE</b><small>COMPUTACIÓN & TECNOLOGÍA</small></span></a><div class="links"><a href="{{ url_for('home') }}">Tienda</a>{% if session.get('admin') %}<a href="{{ url_for('dashboard') }}">Administración</a><a href="{{ url_for('reports') }}">Reportes</a><a class="btn light" href="{{ url_for('logout') }}">Salir</a>{% else %}<a href="{{ url_for('login') }}">Acceso admin</a>{% endif %}</div></div></nav>
{% with messages=get_flashed_messages() %}{% if messages %}<div class="wrap" style="padding-bottom:0">{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}</div>{% endif %}{% endwith %}
{{ body|safe }}<footer class="footer"><b>UPRIT TECH STORE</b><br>Universidad Privada de Trujillo · Proyecto académico de desarrollo web<br><br>© 2026 · Flask + Python + SQLite</footer></body></html>
"""

def page(title, body, **ctx):
    return render_template_string(BASE, title=title, body=render_template_string(body, **ctx), **ctx)

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            flash("Inicia sesión para acceder al panel administrativo.")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

@app.route("/")
def home():
    with db() as con: products=con.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    body = """
    <main class="wrap"><section class="hero"><div><div class="eyebrow">UPRIT UNIVERSITY · TECH STORE</div><h1>Potencia tu mundo.<br><span style="color:#ffd6df">Equipa tu futuro.</span></h1><p>Encuentra periféricos y componentes para llevar tu setup al siguiente nivel. Tecnología, rendimiento y estilo en un solo lugar.</p><a class="btn" style="background:#fff;color:#941b38;margin-top:10px" href="#catalogo">EXPLORAR PRODUCTOS&nbsp; ↘</a></div><div class="heroart">🖥️</div></section>
    <div class="sectionhead" id="catalogo"><div><div class="eyebrow" style="color:#a51e3b">SELECCIÓN TECNOLÓGICA</div><h2>Catálogo destacado</h2><div class="muted">Encuentra el equipo ideal para ti.</div></div><span class="muted">{{products|length}} productos</span></div>
    <div class="grid">{% for p in products %}<article class="product"><div class="picon">{{p.icon}}</div><div class="tag">{{p.category}}</div><h3>{{p.name}}</h3><p>{{p.description}}</p><div class="price">S/ {{'%.2f'|format(p.price)}}</div><div class="stock">{% if p.stock>0 %}{{p.stock}} unidades disponibles{% else %}Agotado{% endif %}</div>{% if p.stock>0 %}<form method="post" action="{{url_for('checkout',product_id=p.id)}}"><input type="number" name="quantity" min="1" max="{{p.stock}}" value="1"><button class="btn">Registrar compra</button></form>{% else %}<button class="btn light" disabled>Sin stock</button>{% endif %}</article>{% else %}<div class="empty">Aún no hay productos publicados.</div>{% endfor %}</div>
    <div class="panel" style="margin-top:30px;background:#191a24;color:white;border:0;display:flex;justify-content:space-between;align-items:center;gap:20px"><div><div class="eyebrow">¿ADMINISTRAS LA TIENDA?</div><h2 style="font:700 23px 'Space Grotesk';margin:7px 0">Gestiona productos y ventas desde un solo lugar.</h2><div style="color:#c8cad2;font-size:13px">Accede al panel para controlar inventario y revisar resultados.</div></div><a class="btn" href="{{url_for('login')}}">PANEL ADMINISTRATIVO</a></div></main>"""
    return page("Tienda",body,products=products)

@app.route("/comprar/<int:product_id>",methods=["POST"])
def checkout(product_id):
    qty=max(1,int(request.form.get("quantity",1)))
    with db() as con:
        p=con.execute("SELECT * FROM products WHERE id=?",(product_id,)).fetchone()
        if not p: abort(404)
        if p["stock"]<qty:
            flash("No hay stock suficiente para completar la compra.")
        else:
            con.execute("UPDATE products SET stock=stock-? WHERE id=?",(qty,product_id))
            con.execute("INSERT INTO sales(product_id,product_name,quantity,unit_price,total,customer,sale_date) VALUES(?,?,?,?,?,?,?)",(p["id"],p["name"],qty,p["price"],qty*p["price"],"Compra web",date.today().isoformat()))
            flash("¡Compra registrada! El inventario se actualizó correctamente.")
    return redirect(url_for("home"))

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        if request.form.get("username")==ADMIN_USER and request.form.get("password")==ADMIN_PASSWORD:
            session["admin"]=True; return redirect(url_for("dashboard"))
        flash("Usuario o contraseña incorrectos.")
    body="""<main class="wrap login"><div class="panel"><div class="brand"><img src="{{url_for('static',filename='uprit-mark.svg')}}"><span><b>UPRIT TECH STORE</b><small>ACCESO ADMINISTRATIVO</small></span></div><h1>Bienvenido de nuevo</h1><p class="muted">Ingresa tus credenciales para gestionar la tienda.</p><form method="post"><div class="field" style="margin:18px 0"><label>Usuario</label><input name="username" required placeholder="admin"></div><div class="field" style="margin:18px 0"><label>Contraseña</label><input name="password" type="password" required placeholder="••••••••"></div><button class="btn" style="width:100%">INICIAR SESIÓN</button></form><p class="muted" style="margin-top:18px;font-size:11px">Acceso de demostración: admin / 123</p></div></main>"""
    return page("Acceso",body)

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("home"))

@app.route("/admin")
@admin_required
def dashboard():
    with db() as con:
        products=con.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        sales=con.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 6").fetchall()
        total=con.execute("SELECT COALESCE(SUM(total),0) FROM sales").fetchone()[0]
        units=con.execute("SELECT COALESCE(SUM(stock),0) FROM products").fetchone()[0]
        count=con.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    body="""<main class="wrap"><div class="pagehead"><h1>Panel de control</h1><div class="muted">Resumen general de UPRIT Tech Store.</div></div>{{nav|safe}}<div class="stats"><div class="stat"><small>VENTAS ACUMULADAS</small><strong>S/ {{'%.2f'|format(total)}}</strong></div><div class="stat"><small>PRODUCTOS EN CATÁLOGO</small><strong>{{products|length}}</strong></div><div class="stat"><small>UNIDADES EN STOCK</small><strong>{{units}}</strong></div></div><div class="panel"><div class="sectionhead" style="margin:0 0 12px"><h2 style="font-size:20px">Productos registrados</h2><a class="btn" href="{{url_for('new_product')}}">+ Nuevo producto</a></div><div style="overflow:auto"><table><tr><th>Producto</th><th>Categoría</th><th>Precio</th><th>Stock</th><th>Acciones</th></tr>{% for p in products %}<tr><td>{{p.icon}} {{p.name}}</td><td>{{p.category}}</td><td>S/ {{'%.2f'|format(p.price)}}</td><td>{{p.stock}}</td><td><div class="actions"><a class="btn light" href="{{url_for('edit_product',pid=p.id)}}">Editar</a><form class="inline" method="post" action="{{url_for('delete_product',pid=p.id)}}" onsubmit="return confirm('¿Eliminar producto?')"><button class="btn dark">Borrar</button></form></div></td></tr>{% endfor %}</table></div></div><div class="panel"><h2 style="font:700 20px 'Space Grotesk'">Últimas ventas</h2>{% if sales %}<table><tr><th>Fecha</th><th>Producto</th><th>Cant.</th><th>Total</th></tr>{% for s in sales %}<tr><td>{{s.sale_date}}</td><td>{{s.product_name}}</td><td>{{s.quantity}}</td><td>S/ {{'%.2f'|format(s.total)}}</td></tr>{% endfor %}</table>{% else %}<div class="empty">Todavía no se registran ventas.</div>{% endif %}</div></main>"""
    return page("Administración",body,nav=admin_nav("dashboard"),products=products,sales=sales,total=total,units=units,count=count)

def admin_nav(active):
    links=[("dashboard","Resumen","dashboard"),("new_product","Nuevo producto","new_product"),("reports","Reportes","reports")]
    return '<div class="adminnav">'+"".join(f'<a class="{"active" if active==ep else ""}" href="{url_for(ep)}">{label}</a>' for ep,label,ep in links)+'</div>'

@app.route("/admin/producto/nuevo",methods=["GET","POST"])
@admin_required
def new_product():
    if request.method=="POST":
        with db() as con: con.execute("INSERT INTO products(name,category,description,price,stock,icon) VALUES(?,?,?,?,?,?)",(request.form["name"],request.form["category"],request.form.get("description",""),float(request.form["price"]),int(request.form["stock"]),request.form.get("icon","💻")))
        flash("Producto agregado al catálogo."); return redirect(url_for("dashboard"))
    return product_form("Nuevo producto")

@app.route("/admin/producto/<int:pid>/editar",methods=["GET","POST"])
@admin_required
def edit_product(pid):
    with db() as con: p=con.execute("SELECT * FROM products WHERE id=?",(pid,)).fetchone()
    if not p: abort(404)
    if request.method=="POST":
        with db() as con: con.execute("UPDATE products SET name=?,category=?,description=?,price=?,stock=?,icon=? WHERE id=?",(request.form["name"],request.form["category"],request.form.get("description",""),float(request.form["price"]),int(request.form["stock"]),request.form.get("icon","💻"),pid))
        flash("Producto actualizado."); return redirect(url_for("dashboard"))
    return product_form("Editar producto",p)

def product_form(title,p=None):
    body="""<main class="wrap"><div class="pagehead"><h1>{{title}}</h1><div class="muted">Completa los datos del producto.</div></div>{{nav|safe}}<div class="panel"><form method="post" class="formgrid"><div class="field"><label>Nombre del producto</label><input name="name" required value="{{p.name if p else ''}}"></div><div class="field"><label>Categoría</label><select name="category">{% for c in ['Periféricos','Componentes','Monitores','Almacenamiento','Audio','Accesorios'] %}<option {% if p and p.category==c %}selected{% endif %}>{{c}}</option>{% endfor %}</select></div><div class="field full"><label>Descripción</label><textarea name="description">{{p.description if p else ''}}</textarea></div><div class="field"><label>Precio (S/)</label><input type="number" step="0.01" min="0" name="price" required value="{{p.price if p else ''}}"></div><div class="field"><label>Stock disponible</label><input type="number" min="0" name="stock" required value="{{p.stock if p else 0}}"></div><div class="field"><label>Ícono / emoji</label><input name="icon" value="{{p.icon if p else '💻'}}"></div><div class="field full"><button class="btn">GUARDAR PRODUCTO</button> <a class="btn light" href="{{url_for('dashboard')}}">Cancelar</a></div></form></div></main>"""
    return page(title,body,title=title,p=p,nav=admin_nav("new_product"))

@app.route("/admin/producto/<int:pid>/eliminar",methods=["POST"])
@admin_required
def delete_product(pid):
    with db() as con: con.execute("DELETE FROM products WHERE id=?",(pid,))
    flash("Producto eliminado."); return redirect(url_for("dashboard"))

@app.route("/admin/reportes")
@admin_required
def reports():
    start=request.args.get("desde",date.today().replace(day=1).isoformat())
    end=request.args.get("hasta",date.today().isoformat())
    with db() as con:
        rows=con.execute("SELECT * FROM sales WHERE sale_date BETWEEN ? AND ? ORDER BY sale_date DESC,id DESC",(start,end)).fetchall()
        total=sum(r["total"] for r in rows); units=sum(r["quantity"] for r in rows)
    body="""<main class="wrap"><div class="pagehead"><h1>Reportes de ventas</h1><div class="muted">Consulta el rendimiento de tu tienda por periodo.</div></div>{{nav|safe}}<div class="panel"><form class="formgrid"><div class="field"><label>Desde</label><input type="date" name="desde" value="{{start}}"></div><div class="field"><label>Hasta</label><input type="date" name="hasta" value="{{end}}"></div><div class="field full"><button class="btn">GENERAR REPORTE</button> <button type="button" class="btn light" onclick="window.print()">Imprimir / Guardar PDF</button></div></form></div><div class="stats"><div class="stat"><small>INGRESOS DEL PERIODO</small><strong>S/ {{'%.2f'|format(total)}}</strong></div><div class="stat"><small>OPERACIONES</small><strong>{{rows|length}}</strong></div><div class="stat"><small>UNIDADES VENDIDAS</small><strong>{{units}}</strong></div></div><div class="panel"><h2 style="font:700 20px 'Space Grotesk'">Detalle de ventas</h2>{% if rows %}<div style="overflow:auto"><table><tr><th>Fecha</th><th>Producto</th><th>Cliente</th><th>Cantidad</th><th>Precio unit.</th><th>Total</th></tr>{% for s in rows %}<tr><td>{{s.sale_date}}</td><td>{{s.product_name}}</td><td>{{s.customer}}</td><td>{{s.quantity}}</td><td>S/ {{'%.2f'|format(s.unit_price)}}</td><td><b>S/ {{'%.2f'|format(s.total)}}</b></td></tr>{% endfor %}</table></div>{% else %}<div class="empty">No hay ventas en el periodo seleccionado.</div>{% endif %}</div></main>"""
    return page("Reportes",body,nav=admin_nav("reports"),start=start,end=end,rows=rows,total=total,units=units)

@app.errorhandler(404)
def not_found(e): return page("No encontrado",'<main class="wrap"><div class="panel"><h1>No encontramos esta página.</h1><a class="btn" href="/">Volver a la tienda</a></div></main>'),404

init_db()
if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG")=="1", host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
