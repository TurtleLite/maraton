import io
import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file
import openpyxl

app = Flask(__name__)
app.static_folder = "static"

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
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; background: #f0f2f5; min-height: 100vh; padding: 30px 20px; color: #1a1a2e; transition: background .3s, color .3s; }
.container { max-width: 960px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.04); border: 1px solid #e8ecf0; animation: fadeUp .45s ease-out; }
.header { display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-bottom: 24px; }
.header img { height: 90px; width: auto; object-fit: contain; }
.header h1 { font-size: 1.5rem; color: #1a1a2e; text-align: center; flex: 1; font-weight: 700; letter-spacing: -.02em; }
.barra { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.barra button, .barra input { padding: 8px 14px; font-size: .875rem; border-radius: 6px; border: 1px solid #d4d8dd; outline: none; font-family: inherit; }
.barra input:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.12); }
.barra button { background: #2563eb; color: #fff; border: none; cursor: pointer; font-weight: 500; transition: background .15s, box-shadow .15s; }
.barra button:hover { background: #1d4ed8; box-shadow: 0 1px 3px rgba(37,99,235,.25); }
.barra button:active { background: #1e40af; transform: scale(.97); }
.barra button:disabled { opacity: .4; cursor: not-allowed; box-shadow: none; }
.barra button.verde { background: #059669; }
.barra button.verde:hover { background: #047857; box-shadow: 0 1px 3px rgba(5,150,105,.25); }
.barra button.verde:active { background: #065f46; transform: scale(.97); }
.barra button.rojo { background: #dc2626; }
.barra button.rojo:hover { background: #b91c1c; box-shadow: 0 1px 3px rgba(220,38,38,.25); }
.barra button.rojo:active { background: #991b1b; transform: scale(.97); }
.barra input { flex: 1; min-width: 100px; background: #f8f9fa; transition: background .15s, border-color .15s, box-shadow .15s; }
.barra input:focus { background: #fff; }
.estado { padding: 8px 16px; border-radius: 6px; margin-bottom: 20px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; font-size: .875rem; border: 1px solid; }
.estado.parada { background: #fffbeb; color: #92400e; border-color: #fde68a; }
.estado.andando { background: #f0fdf4; color: #065f46; border-color: #a7f3d0; }
.separador { height: 1px; background: #e8ecf0; margin: 20px 0; }
.buscar-wrap { margin-bottom: 12px; }
.buscar-wrap input { width: 100%; padding: 10px 14px; font-size: .875rem; border-radius: 6px; border: 1px solid #d4d8dd; outline: none; font-family: inherit; background: #f8f9fa; transition: background .15s, border-color .15s, box-shadow .15s; }
.buscar-wrap input:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.12); background: #fff; }
table { width: 100%; border-collapse: collapse; font-size: .85rem; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #e8ecf0; }
th { background: #f8f9fa; font-weight: 600; color: #475569; position: sticky; top: 0; font-size: .8rem; text-transform: uppercase; letter-spacing: .03em; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #f8f9fa; }
tbody tr:nth-child(even) td { background: #fafbfc; }
tbody tr:nth-child(even):hover td { background: #f1f3f5; }
td button { transition: background .15s, transform .15s; }
td button:active { transform: scale(.9); }
.tabla-wrap { max-height: 500px; overflow-y: auto; border-radius: 8px; border: 1px solid #e8ecf0; }
.contador { font-size: .8rem; color: #64748b; margin-bottom: 10px; }
.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%) translateY(10px); background: #1e293b; color: #f1f5f9; padding: 12px 24px; border-radius: 8px; font-weight: 500; font-size: .875rem; box-shadow: 0 4px 16px rgba(0,0,0,.2); z-index: 999; opacity: 0; transition: opacity .25s, transform .25s; pointer-events: none; }
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
.footer { position: fixed; bottom: 12px; left: 0; right: 0; display: flex; justify-content: space-between; padding: 0 24px; font-size: .65rem; color: rgba(0,0,0,.25); pointer-events: none; z-index: 0; letter-spacing: .04em; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.35); display: flex; align-items: center; justify-content: center; z-index: 1000; opacity: 0; transition: opacity .2s; pointer-events: none; }
.modal-overlay.show { opacity: 1; pointer-events: auto; }
.modal-card { background: #fff; border-radius: 12px; padding: 28px 32px; max-width: 420px; width: 90%; box-shadow: 0 8px 40px rgba(0,0,0,.18); text-align: center; }
.modal-card p { font-size: .95rem; color: #1a1a2e; margin-bottom: 22px; line-height: 1.55; white-space: pre-wrap; }
.modal-overlay.show .modal-card { animation: modalIn .25s ease-out; }
.modal-card .botones { display: flex; gap: 10px; justify-content: center; }
.modal-card button { padding: 9px 22px; border-radius: 6px; border: none; font-weight: 500; font-size: .875rem; cursor: pointer; transition: background .15s; font-family: inherit; }
.modal-card .btn-si { background: #059669; color: #fff; }
.modal-card .btn-si:hover { background: #047857; }
.modal-card .btn-no { background: #e5e7eb; color: #475569; }
.modal-card .btn-no:hover { background: #d1d5db; }
.modal-card .btn-ok { background: #2563eb; color: #fff; min-width: 100px; }
.modal-card .btn-ok:hover { background: #1d4ed8; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
@keyframes rowIn { from { opacity: 0; transform: translateX(-12px); } to { opacity: 1; transform: translateX(0); } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .4; } }
@keyframes modalIn { from { opacity: 0; transform: scale(.92); } to { opacity: 1; transform: scale(1); } }
.estado.andando::before { content: ''; display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #059669; animation: pulse 1.8s ease-in-out infinite; margin-right: 4px; }
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
  <div id="estado-carrera" class="estado parada">⏸ Carrera no iniciada</div>
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
      tr.style.animation = 'rowIn .35s ease-out both';
      tr.style.animationDelay = (i * 0.035) + 's';
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
      est.textContent = '🏁 Carrera en curso — Salida: ' + d.hora_inicio;
      est.className = 'estado andando';
      document.getElementById('btn-iniciar').disabled = true;
      document.getElementById('btn-finalizar').style.display = '';
    } else {
      est.textContent = '⏸ Carrera no iniciada';
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
cargar();
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML, logo_izq=LOGO_IZQ, logo_der=LOGO_DER)

@app.route("/api/datos")
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
