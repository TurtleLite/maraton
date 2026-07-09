import io
import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file, session, redirect
from functools import wraps
import openpyxl

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "burroton2026")
app.static_folder = "static"

LOGIN_USER = os.environ.get("LOGIN_USER", "admin")
LOGIN_PASS = os.environ.get("LOGIN_PASS", "burroton2026")

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            if request.path.startswith("/api/"):
                return jsonify(error="Acceso no autorizado"), 401
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

LOGIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Burrotón San Benito José — Acceso</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
.login-card { background: #fff; border-radius: 12px; padding: 40px 36px; width: 360px; max-width: 90%; box-shadow: 0 1px 3px rgba(0,0,0,.08); border: 1px solid #e8ecf0; text-align: center; }
.login-card h1 { font-size: 1.3rem; color: #1a1a2e; margin-bottom: 6px; }
.login-card p { font-size: .85rem; color: #64748b; margin-bottom: 24px; }
.login-card input { width: 100%; padding: 10px 14px; font-size: .875rem; border-radius: 6px; border: 1px solid #d4d8dd; outline: none; font-family: inherit; margin-bottom: 12px; background: #f8f9fa; transition: background .15s, border-color .15s; }
.login-card input:focus { border-color: #2563eb; background: #fff; box-shadow: 0 0 0 2px rgba(37,99,235,.12); }
.login-card button { width: 100%; padding: 10px; font-size: .875rem; border-radius: 6px; border: none; background: #2563eb; color: #fff; font-weight: 500; cursor: pointer; font-family: inherit; }
.login-card button:hover { background: #1d4ed8; }
.login-card .error { color: #dc2626; font-size: .8rem; margin-bottom: 12px; }
</style>
</head>
<body>
<div class="login-card">
  <h1>Burrotón San Benito José</h1>
  <p>Ingresa tus credenciales</p>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST">
    <input type="text" name="user" placeholder="Usuario" required autocomplete="username">
    <input type="password" name="pass" placeholder="Contraseña" required autocomplete="current-password">
    <button type="submit">Ingresar</button>
  </form>
</div>
</body>
</html>"""

DB_URL = os.environ.get("DATABASE_URL", "postgresql://maraton_db_yu80_user:PGKNIB3F5HTynSqz7Vx6x01vJcQVG3bD@dpg-d97vq9qabeoc739aqnmg-a.virginia-postgres.render.com/maraton_db_yu80?sslmode=require")

def get_db():
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=10)
        conn.autocommit = True
        return conn
    except Exception as e:
        print("DB error:", e)
        return None

def init_db():
    conn = get_db()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS carrera (id SERIAL PRIMARY KEY, iniciada BOOLEAN DEFAULT FALSE, hora_inicio TIMESTAMP)")
        cur.execute("CREATE TABLE IF NOT EXISTS corredores (id SERIAL PRIMARY KEY, dorsal VARCHAR(20) UNIQUE NOT NULL, nombre VARCHAR(200) NOT NULL, tiempo_llegada TIMESTAMP, posicion INTEGER)")
        cur.execute("SELECT COUNT(*) FROM carrera")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO carrera (iniciada) VALUES (FALSE)")
        cur.close()
    except Exception as e:
        print("init_db error:", e)
    finally:
        conn.close()

LOGO_IZQ = "/static/BURROTON 2026.png"
LOGO_DER = "/static/LOGO SAN BENITO JOSE.jpg"

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Burrotón San Benito José</title>
<link rel="icon" href="/static/BURROTON 2026.png">
<style>
:root { --bg: #f0f2f5; --surface: #fff; --border: #e8ecf0; --text: #1a1a2e; --text2: #475569; --text3: #64748b; --input-bg: #f8f9fa; --input-border: #d4d8dd; --primary: #2563eb; --primary-hover: #1d4ed8; --primary-active: #1e40af; --green: #059669; --green-hover: #047857; --red: #dc2626; --red-hover: #b91c1c; --row-hover: #f8f9fa; --row-alt: #fafbfc; --shadow: 0 1px 3px rgba(0,0,0,.08); --shadow-lg: 0 8px 40px rgba(0,0,0,.18); --toast-bg: #1e293b; --toast-text: #f1f5f9; --modal-overlay: rgba(0,0,0,.35); }
.dark { --bg: #0f172a; --surface: #1e293b; --border: #334155; --text: #f1f5f9; --text2: #94a3b8; --text3: #64748b; --input-bg: #1e293b; --input-border: #475569; --primary: #3b82f6; --primary-hover: #2563eb; --primary-active: #1d4ed8; --green: #10b981; --green-hover: #059669; --red: #ef4444; --red-hover: #dc2626; --row-hover: #334155; --row-alt: #293548; --shadow: 0 1px 3px rgba(0,0,0,.2); --shadow-lg: 0 8px 40px rgba(0,0,0,.4); --toast-bg: #0f172a; --toast-text: #e2e8f0; --modal-overlay: rgba(0,0,0,.6); }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; background: var(--bg); min-height: 100vh; padding: 30px 20px; color: var(--text); transition: background .3s, color .3s; }
.container { max-width: 960px; margin: 0 auto; background: var(--surface); border-radius: 12px; padding: 32px; box-shadow: var(--shadow), 0 1px 2px rgba(0,0,0,.04); border: 1px solid var(--border); transition: background .3s, border-color .3s, box-shadow .3s; animation: fadeUp .4s ease-out; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
.header { display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-bottom: 24px; }
.header img { height: 90px; width: auto; object-fit: contain; transition: opacity .3s; }
.dark .header img { opacity: .85; }
.header h1 { font-size: 1.5rem; color: var(--text); text-align: center; flex: 1; font-weight: 700; letter-spacing: -.02em; transition: color .3s; }
.theme-btn { position: fixed; top: 14px; right: 14px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 7px 11px; cursor: pointer; font-size: 1.1rem; color: var(--text2); transition: background .2s, color .2s, border-color .2s, transform .2s, box-shadow .2s; z-index: 100; box-shadow: var(--shadow); }
.theme-btn:hover { background: var(--row-hover); color: var(--text); transform: rotate(15deg) scale(1.05); box-shadow: var(--shadow), 0 2px 8px rgba(0,0,0,.1); }
.barra { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.barra button, .barra input { padding: 8px 14px; font-size: .875rem; border-radius: 6px; border: 1px solid var(--input-border); outline: none; font-family: inherit; transition: background .2s, border-color .2s, box-shadow .2s, color .2s; }
.barra input:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(37,99,235,.12); }
.barra button { background: var(--primary); color: #fff; border: none; cursor: pointer; font-weight: 500; transition: background .2s, box-shadow .2s, transform .1s; }
.barra button:hover { background: var(--primary-hover); box-shadow: 0 2px 8px rgba(37,99,235,.25); }
.barra button:active { transform: scale(.97); }
.barra button:disabled { opacity: .4; cursor: not-allowed; box-shadow: none; transform: none; }
.barra button.verde { background: var(--green); }
.barra button.verde:hover { background: var(--green-hover); }
.barra button.rojo { background: var(--red); }
.barra button.rojo:hover { background: var(--red-hover); }
.barra input { flex: 1; min-width: 100px; background: var(--input-bg); color: var(--text); }
.barra input:focus { background: var(--surface); }
.estado { padding: 8px 16px; border-radius: 6px; margin-bottom: 20px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; font-size: .875rem; border: 1px solid; transition: background .3s, color .3s, border-color .3s; }
.estado.parada { background: #fffbeb; color: #92400e; border-color: #fde68a; }
.dark .estado.parada { background: #422006; color: #fde68a; border-color: #78350f; }
.estado.andando { background: #f0fdf4; color: #065f46; border-color: #a7f3d0; }
.dark .estado.andando { background: #052e16; color: #a7f3d0; border-color: #166534; }
.estado.andando .pulse { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #059669; animation: pulse 1.5s ease-in-out infinite; }
.dark .estado.andando .pulse { background: #10b981; }
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: .5; transform: scale(.75); } }
.separador { height: 1px; background: var(--border); margin: 20px 0; transition: background .3s; }
.buscar-wrap { margin-bottom: 12px; }
.buscar-wrap input { width: 100%; padding: 10px 14px; font-size: .875rem; border-radius: 6px; border: 1px solid var(--input-border); outline: none; font-family: inherit; background: var(--input-bg); color: var(--text); transition: background .2s, border-color .2s, box-shadow .2s, color .2s; }
.buscar-wrap input:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(37,99,235,.12); background: var(--surface); }
table { width: 100%; border-collapse: collapse; font-size: .85rem; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); transition: background .2s, border-color .3s, color .3s; }
th { background: var(--row-hover); font-weight: 600; color: var(--text2); position: sticky; top: 0; font-size: .8rem; text-transform: uppercase; letter-spacing: .03em; }
tr:last-child td { border-bottom: none; }
tbody tr { animation: rowIn .3s ease-out both; }
@keyframes rowIn { from { opacity: 0; transform: translateX(-8px); } to { opacity: 1; transform: translateX(0); } }
tbody tr:nth-child(1) { animation-delay: 0s; }
tbody tr:nth-child(2) { animation-delay: .03s; }
tbody tr:nth-child(3) { animation-delay: .06s; }
tbody tr:nth-child(4) { animation-delay: .09s; }
tbody tr:nth-child(5) { animation-delay: .12s; }
tbody tr:nth-child(6) { animation-delay: .15s; }
tbody tr:nth-child(n+7) { animation-delay: .18s; }
tr:hover td { background: var(--row-hover); }
tbody tr:nth-child(even) td { background: var(--row-alt); }
tbody tr:nth-child(even):hover td { background: var(--row-hover); }
td button { transition: background .15s, transform .1s; }
td button:active { transform: scale(.9); }
.tabla-wrap { max-height: 500px; overflow-y: auto; border-radius: 8px; border: 1px solid var(--border); transition: border-color .3s; }
.contador { font-size: .8rem; color: var(--text3); margin-bottom: 10px; transition: color .3s; }
.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%) translateY(10px); background: var(--toast-bg); color: var(--toast-text); padding: 12px 24px; border-radius: 8px; font-weight: 500; font-size: .875rem; box-shadow: 0 4px 16px rgba(0,0,0,.2); z-index: 999; opacity: 0; transition: opacity .25s, transform .25s; pointer-events: none; }
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
.footer { position: fixed; bottom: 12px; left: 0; right: 0; display: flex; justify-content: space-between; padding: 0 24px; font-size: .65rem; color: var(--text3); pointer-events: none; z-index: 0; letter-spacing: .04em; transition: color .3s; }
.footer a { pointer-events: auto; }
.modal-overlay { position: fixed; inset: 0; background: var(--modal-overlay); display: flex; align-items: center; justify-content: center; z-index: 1000; opacity: 0; transition: opacity .2s; pointer-events: none; }
.modal-overlay.show { opacity: 1; pointer-events: auto; }
.modal-card { background: var(--surface); border-radius: 12px; padding: 28px 32px; max-width: 420px; width: 90%; box-shadow: var(--shadow-lg); text-align: center; transition: background .3s; animation: modalIn .25s ease-out; }
@keyframes modalIn { from { opacity: 0; transform: scale(.92) translateY(8px); } to { opacity: 1; transform: scale(1) translateY(0); } }
.modal-card p { font-size: .95rem; color: var(--text); margin-bottom: 22px; line-height: 1.55; white-space: pre-wrap; transition: color .3s; }
.modal-card .botones { display: flex; gap: 10px; justify-content: center; }
.modal-card button { padding: 9px 22px; border-radius: 6px; border: none; font-weight: 500; font-size: .875rem; cursor: pointer; transition: background .15s, transform .1s; font-family: inherit; }
.modal-card button:active { transform: scale(.97); }
.modal-card .btn-si { background: var(--green); color: #fff; }
.modal-card .btn-si:hover { background: var(--green-hover); }
.modal-card .btn-no { background: #e5e7eb; color: #475569; }
.dark .modal-card .btn-no { background: #475569; color: #e2e8f0; }
.modal-card .btn-no:hover { background: #d1d5db; }
.dark .modal-card .btn-no:hover { background: #64748b; }
.modal-card .btn-ok { background: var(--primary); color: #fff; min-width: 100px; }
.modal-card .btn-ok:hover { background: var(--primary-hover); }
@media (max-width: 600px) {
  .container { padding: 20px; }
  .header h1 { font-size: 1.1rem; }
  .header img { height: 60px; }
  .barra button, .barra input { font-size: .8rem; padding: 7px 10px; }
}
</style>
</head>
<body>
<div class="container" id="app">
  <div class="header">
    <img src="{{ logo_izq }}" alt="Logo">
    <h1>Burrotón San Benito José</h1>
    <img src="{{ logo_der }}" alt="Logo">
  </div>
  <div id="estado-carrera" class="estado parada"><span class="pulse"></span>⏸ Carrera no iniciada</div>
  <div class="barra">
    <input id="dorsal-input" placeholder="Número" size="6">
    <input id="nombre-input" placeholder="Nombre del corredor">
    <button onclick="registrar(this)">Registrar</button>
    <button id="btn-iniciar" class="verde" onclick="iniciar()">Iniciar carrera</button>
    <button id="btn-finalizar" class="rojo" onclick="finalizar()" style="display:none">Finalizar carrera</button>
  </div>
  <div class="barra">
    <input id="llegada-input" placeholder="Número del que llega">
    <button class="verde" onclick="llegada(this)">Registrar llegada</button>
    <button onclick="resultados()">Ver resultados</button>
    <button onclick="reporte()">Descargar reporte</button>
    <button onclick="document.getElementById('excel-input').click()">Importar Excel</button>
    <input type="file" id="excel-input" accept=".xlsx" style="display:none" onchange="importarExcel(this.files[0])">
  </div>
  <div class="separador"></div>
  <div class="buscar-wrap">
    <input id="buscar-input" placeholder="Buscar por número o nombre..." oninput="cargar()">
  </div>
  <div class="contador" id="contador"></div>
  <div class="tabla-wrap">
    <table>
      <thead><tr><th>Núm.</th><th>Nombre</th><th>Llegada</th><th>Posición</th><th>Acción</th></tr></thead>
      <tbody id="tabla"></tbody>
    </table>
  </div>
</div>
<button class="theme-btn" id="theme-btn" onclick="toggleTheme()" title="Modo oscuro">🌙</button>
<div class="footer"><span>FIXTLE</span><span>TURTLELITE</span></div>
<div id="toast" class="toast"></div>
<div class="modal-overlay" id="modal">
  <div class="modal-card">
    <p id="modal-msg"></p>
    <div class="botones" id="modal-botones"></div>
  </div>
</div>
<script>
function cargar() {
  const q = document.getElementById('buscar-input').value.trim();
  const url = q ? '/api/buscar?q=' + encodeURIComponent(q) : '/api/datos';
  fetch(url).then(r=>r.json()).then(d=>{
    const tbody = document.getElementById('tabla');
    tbody.innerHTML = '';
    (d.corredores||[]).forEach((c, i) => {
      const tr = document.createElement('tr');
      tr.style.animationDelay = (i * 0.03) + 's';
      const llegada = c.tiempo_llegada || '—';
      const pos = c.posicion ? '#' + c.posicion : '—';
      tr.innerHTML = '<td>' + c.dorsal + '</td><td>' + c.nombre + '</td><td>' + llegada + '</td><td>' + pos + '</td><td></td>';
      const btn = document.createElement('button');
      btn.className = 'rojo';
      btn.style.cssText = 'padding:4px 10px;font-size:.8rem';
      btn.textContent = '✕';
      btn.onclick = () => borrar(c.dorsal);
      tr.lastChild.appendChild(btn);
      tbody.appendChild(tr);
    });
    document.getElementById('contador').textContent = 'Total: ' + (d.corredores||[]).length + ' corredores';
    const est = document.getElementById('estado-carrera');
    if (d.carrera_iniciada) {
      est.innerHTML = '<span class="pulse"></span>🏁 Carrera en curso — Salida: ' + d.hora_inicio;
      est.className = 'estado andando';
      document.getElementById('btn-iniciar').disabled = true;
      document.getElementById('btn-finalizar').style.display = '';
    } else {
      est.innerHTML = '<span class="pulse"></span>⏸ Carrera no iniciada';
      est.className = 'estado parada';
      document.getElementById('btn-iniciar').disabled = false;
      document.getElementById('btn-finalizar').style.display = 'none';
    }
  });
}
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 3000);
}
function mostrarModal(msg) {
  const modal = document.getElementById('modal');
  document.getElementById('modal-msg').textContent = msg;
  document.getElementById('modal-botones').innerHTML = '<button class="btn-ok" onclick="cerrarModal()">Aceptar</button>';
  modal.classList.add('show');
}
function cerrarModal() {
  document.getElementById('modal').classList.remove('show');
}
function confirmarModal(msg) {
  return new Promise(resolve => {
    const modal = document.getElementById('modal');
    document.getElementById('modal-msg').textContent = msg;
    document.getElementById('modal-botones').innerHTML =
      '<button class="btn-si" onclick="cerrarModal(); resolveConfirm(true)">Sí</button>' +
      '<button class="btn-no" onclick="cerrarModal(); resolveConfirm(false)">No</button>';
    modal.classList.add('show');
    window.resolveConfirm = resolve;
  });
}
function _fetch(url, opts, btn) {
  if (btn) btn.disabled = true;
  return fetch(url, opts).then(r=>r.json()).finally(() => { if(btn) btn.disabled = false; });
}
function registrar(btn) {
  const dorsal = document.getElementById('dorsal-input').value.trim();
  const nombre = document.getElementById('nombre-input').value.trim();
  if (!dorsal || !nombre) return mostrarModal('Completa número y nombre.');
  _fetch('/api/registrar', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({dorsal, nombre}) }, btn)
    .then(d=> { if(d.error) mostrarModal(d.error); else { document.getElementById('dorsal-input').value=''; document.getElementById('nombre-input').value=''; toast('Corredor registrado'); cargar(); } });
}
function iniciar() {
  const btn = document.getElementById('btn-iniciar');
  btn.disabled = true;
  _fetch('/api/iniciar', {method:'POST'}, btn).then(d=> { if(d.error) mostrarModal(d.error); else { toast('Carrera iniciada'); cargar(); } });
}
function llegada(btn) {
  const dorsal = document.getElementById('llegada-input').value.trim();
  if (!dorsal) return mostrarModal('Ingresa un número.');
  _fetch('/api/llegada', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({dorsal})}, btn)
    .then(d=> { if(d.error) mostrarModal(d.error); else { document.getElementById('llegada-input').value=''; cargar(); if(d.mensaje) toast(d.mensaje); } });
}
function finalizar() {
  confirmarModal('¿Finalizar la carrera?').then(r => {
    if (!r) return;
    fetch('/api/finalizar', {method:'POST'}).then(r=>r.json()).then(d=> { if(d.error) mostrarModal(d.error); else toast('Carrera finalizada'); cargar(); });
  });
}
function resultados() {
  fetch('/api/resultados').then(r=>r.json()).then(d=> {
    if(d.error) return mostrarModal(d.error);
    let txt = 'RESULTADOS\\n' + '='.repeat(30) + '\\n';
    d.llegados.forEach(c => { txt += '#' + c.pos + '  ' + c.dorsal + '  ' + c.nombre + '  ' + c.tiempo + '\\n'; });
    mostrarModal(txt);
  });
}
function reporte() {
  window.location.href = '/api/reporte';
}
function borrar(dorsal) {
  confirmarModal('¿Borrar corredor número ' + dorsal + '?').then(r => {
    if (!r) return;
    fetch('/api/borrar', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({dorsal}) })
      .then(r=>r.json()).then(d=> { if(d.error) mostrarModal(d.error); else toast('Corredor eliminado'); cargar(); });
  });
}
function importarExcel(file) {
  if (!file) return;
  const form = new FormData();
  form.append('excel', file);
  fetch('/api/importar_excel', { method:'POST', body: form })
    .then(r=>r.json()).then(d=> { if(d.error) mostrarModal(d.error); else toast(d.mensaje); cargar(); });
}
function toggleTheme() {
  document.body.classList.toggle('dark');
  const btn = document.getElementById('theme-btn');
  btn.textContent = document.body.classList.contains('dark') ? '☀️' : '🌙';
  localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
}
(function() {
  if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark');
    document.getElementById('theme-btn').textContent = '☀️';
  }
})();
cargar();
</script>
</body>
</html>"""

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user", "").strip()
        passw = request.form.get("pass", "").strip()
        if user == LOGIN_USER and passw == LOGIN_PASS:
            session["user"] = user
            return redirect("/")
        return render_template_string(LOGIN_HTML, error="Usuario o contraseña incorrectos.")
    return render_template_string(LOGIN_HTML, error=None)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/")
@login_required
def index():
    return render_template_string(HTML, logo_izq=LOGO_IZQ, logo_der=LOGO_DER)

@app.route("/api/datos")
@login_required
def api_datos():
    init_db()
    conn = get_db()
    if not conn:
        return jsonify(carrera_iniciada=False, hora_inicio=None, corredores=[])
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT dorsal, nombre, tiempo_llegada, posicion FROM corredores ORDER BY id")
        rows = cur.fetchall()
        corredores = []
        for r in rows:
            corredores.append({"dorsal": r["dorsal"], "nombre": r["nombre"], "tiempo_llegada": r["tiempo_llegada"].isoformat() if r["tiempo_llegada"] else None, "posicion": r["posicion"]})
        cur.execute("SELECT iniciada, hora_inicio FROM carrera WHERE id = 1")
        c = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify(carrera_iniciada=c["iniciada"], hora_inicio=c["hora_inicio"].isoformat() if c["hora_inicio"] else None, corredores=corredores)
    except Exception as e:
        print("datos error:", e)
        return jsonify(carrera_iniciada=False, hora_inicio=None, corredores=[])

@app.route("/api/buscar")
@login_required
def api_buscar():
    init_db()
    q = request.args.get("q", "").strip()
    conn = get_db()
    if not conn:
        return jsonify(carrera_iniciada=False, hora_inicio=None, corredores=[])
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT dorsal, nombre, tiempo_llegada, posicion FROM corredores WHERE dorsal ILIKE %s OR nombre ILIKE %s ORDER BY id", (f"%{q}%", f"%{q}%"))
        rows = cur.fetchall()
        corredores = []
        for r in rows:
            corredores.append({"dorsal": r["dorsal"], "nombre": r["nombre"], "tiempo_llegada": r["tiempo_llegada"].isoformat() if r["tiempo_llegada"] else None, "posicion": r["posicion"]})
        cur.execute("SELECT iniciada, hora_inicio FROM carrera WHERE id = 1")
        c = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify(carrera_iniciada=c["iniciada"], hora_inicio=c["hora_inicio"].isoformat() if c["hora_inicio"] else None, corredores=corredores)
    except Exception as e:
        print("buscar error:", e)
        return jsonify(carrera_iniciada=False, hora_inicio=None, corredores=[])

@app.route("/api/registrar", methods=["POST"])
@login_required
def api_registrar():
    init_db()
    dorsal = request.json.get("dorsal", "").strip()
    nombre = request.json.get("nombre", "").strip()
    if not dorsal or not nombre:
        return jsonify(error="Completa todos los campos."), 400
    conn = get_db()
    if not conn:
        return jsonify(error="Base de datos no disponible"), 503
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO corredores (dorsal, nombre) VALUES (%s, %s)", (dorsal, nombre))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(ok=True)
    except psycopg2.errors.UniqueViolation:
        return jsonify(error="Ya existe un corredor con ese número."), 400
    except Exception as e:
        print("registrar error:", e)
        return jsonify(error="Error al registrar"), 500

@app.route("/api/iniciar", methods=["POST"])
@login_required
def api_iniciar():
    init_db()
    conn = get_db()
    if not conn:
        return jsonify(error="Base de datos no disponible"), 503
    try:
        cur = conn.cursor()
        cur.execute("SELECT iniciada FROM carrera WHERE id = 1")
        row = cur.fetchone()
        if row[0]:
            cur.close()
            conn.close()
            return jsonify(error="La carrera ya está iniciada."), 400
        ahora = datetime.now()
        cur.execute("UPDATE carrera SET iniciada = TRUE, hora_inicio = %s WHERE id = 1", (ahora,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(ok=True)
    except Exception as e:
        print("iniciar error:", e)
        return jsonify(error="Error al iniciar carrera"), 500

@app.route("/api/llegada", methods=["POST"])
@login_required
def api_llegada():
    init_db()
    dorsal = request.json.get("dorsal", "").strip()
    conn = get_db()
    if not conn:
        return jsonify(error="Base de datos no disponible"), 503
    try:
        cur = conn.cursor()
        cur.execute("SELECT iniciada FROM carrera WHERE id = 1")
        if not cur.fetchone()[0]:
            cur.close()
            conn.close()
            return jsonify(error="La carrera no ha iniciado."), 400
        cur.execute("SELECT id, nombre, tiempo_llegada FROM corredores WHERE dorsal = %s", (dorsal,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return jsonify(error="Número no encontrado."), 404
        if row[2]:
            cur.close()
            conn.close()
            return jsonify(error=f"{row[1]} ya llegó."), 400
        ahora = datetime.now()
        cur.execute("SELECT COUNT(*) FROM corredores WHERE tiempo_llegada IS NOT NULL")
        posicion = cur.fetchone()[0] + 1
        cur.execute("UPDATE corredores SET tiempo_llegada = %s, posicion = %s WHERE id = %s", (ahora, posicion, row[0]))
        conn.commit()
        cur.execute("SELECT hora_inicio FROM carrera WHERE id = 1")
        inicio = cur.fetchone()[0]
        trans = ahora - inicio
        h, resto = divmod(int(trans.total_seconds()), 3600)
        m, s = divmod(resto, 60)
        cur.close()
        conn.close()
        return jsonify(ok=True, mensaje=f"¡{row[1]} llegó! #{posicion} — {h}h {m}m {s}s")
    except Exception as e:
        print("llegada error:", e)
        return jsonify(error="Error al registrar llegada"), 500

@app.route("/api/resultados")
@login_required
def api_resultados():
    init_db()
    conn = get_db()
    if not conn:
        return jsonify(error="Base de datos no disponible"), 503
    try:
        cur = conn.cursor()
        cur.execute("SELECT hora_inicio FROM carrera WHERE id = 1")
        inicio = cur.fetchone()[0]
        if not inicio:
            cur.close()
            conn.close()
            return jsonify(error="La carrera no ha iniciado."), 400
        cur.execute("SELECT dorsal, nombre, posicion, tiempo_llegada FROM corredores WHERE tiempo_llegada IS NOT NULL ORDER BY posicion")
        rows = cur.fetchall()
        if not rows:
            cur.close()
            conn.close()
            return jsonify(error="Aún no hay llegadas."), 400
        res = []
        for r in rows:
            trans = r[3] - inicio
            h, resto = divmod(int(trans.total_seconds()), 3600)
            m, s = divmod(resto, 60)
            res.append({"pos": r[2], "dorsal": r[0], "nombre": r[1], "tiempo": f"{h}h {m}m {s}s"})
        cur.close()
        conn.close()
        return jsonify(llegados=res)
    except Exception as e:
        print("resultados error:", e)
        return jsonify(error="Error al obtener resultados"), 500

@app.route("/api/finalizar", methods=["POST"])
@login_required
def api_finalizar():
    init_db()
    conn = get_db()
    if not conn:
        return jsonify(error="Base de datos no disponible"), 503
    try:
        cur = conn.cursor()
        cur.execute("SELECT iniciada FROM carrera WHERE id = 1")
        if not cur.fetchone()[0]:
            cur.close()
            conn.close()
            return jsonify(error="La carrera no está iniciada."), 400
        cur.execute("UPDATE carrera SET iniciada = FALSE WHERE id = 1")
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(ok=True)
    except Exception as e:
        print("finalizar error:", e)
        return jsonify(error="Error al finalizar carrera"), 500

@app.route("/api/importar_excel", methods=["POST"])
@login_required
def api_importar_excel():
    init_db()
    if "excel" not in request.files:
        return jsonify(error="No se envió archivo."), 400
    file = request.files["excel"]
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file.read()))
        ws = wb.active
        headers = [cell.value for cell in ws[1]]
        col_dorsal = None
        col_nombre = None
        for i, h in enumerate(headers):
            h_lower = str(h).strip().lower() if h else ""
            if "dorsal" in h_lower or "numero" in h_lower or "num" in h_lower:
                col_dorsal = i
            if "nombre" in h_lower or "corredor" in h_lower:
                col_nombre = i
        if col_dorsal is None or col_nombre is None:
            return jsonify(error="No se encontraron columnas 'Número' y 'Nombre'."), 400
        conn = get_db()
        if not conn:
            return jsonify(error="Base de datos no disponible"), 503
        cur = conn.cursor()
        cont = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            dorsal = str(row[col_dorsal]).strip() if row[col_dorsal] is not None else ""
            nombre = str(row[col_nombre]).strip() if row[col_nombre] is not None else ""
            if not dorsal or not nombre:
                continue
            try:
                cur.execute("INSERT INTO corredores (dorsal, nombre) VALUES (%s, %s)", (dorsal, nombre))
                conn.commit()
                cont += 1
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                continue
        cur.close()
        conn.close()
        return jsonify(mensaje=f"Se importaron {cont} corredores.")
    except Exception as e:
        print("importar excel error:", e)
        return jsonify(error="Error al procesar el Excel"), 500

@app.route("/api/borrar", methods=["POST"])
@login_required
def api_borrar():
    init_db()
    dorsal = request.json.get("dorsal", "").strip()
    if not dorsal:
        return jsonify(error="Número requerido."), 400
    conn = get_db()
    if not conn:
        return jsonify(error="Base de datos no disponible"), 503
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM corredores WHERE dorsal = %s", (dorsal,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(ok=True)
    except Exception as e:
        print("borrar error:", e)
        return jsonify(error="Error al borrar"), 500

@app.route("/api/reporte")
@login_required
def api_reporte():
    init_db()
    conn = get_db()
    if not conn:
        return jsonify(error="Base de datos no disponible"), 503
    try:
        cur = conn.cursor()
        cur.execute("SELECT hora_inicio FROM carrera WHERE id = 1")
        inicio = cur.fetchone()[0]
        if not inicio:
            cur.close()
            conn.close()
            return jsonify(error="La carrera no ha iniciado."), 400
        cur.execute("SELECT posicion, dorsal, nombre, tiempo_llegada FROM corredores WHERE tiempo_llegada IS NOT NULL ORDER BY posicion")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte Burrotón"
        ws.append(["Posición", "Núm.", "Nombre", "Tiempo Llegada", "Tiempo Transcurrido"])
        for r in rows:
            trans = r[3] - inicio
            h, resto = divmod(int(trans.total_seconds()), 3600)
            m, s = divmod(resto, 60)
            ws.append([r[0], r[1], r[2], r[3].isoformat(), f"{h}h {m}m {s}s"])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return send_file(buf, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="reporte_maraton.xlsx")
    except Exception as e:
        print("reporte error:", e)
        return jsonify(error="Error al generar reporte"), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
