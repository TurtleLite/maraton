import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
app.static_folder = "static"

DB_URL = os.environ.get("DATABASE_URL", "postgresql://maraton_db_yu80_user:PGKNIB3F5HTynSqz7Vx6x01vJcQVG3bD@dpg-d97vq9qabeoc739aqnmg-a/maraton_db_yu80")

def get_db():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS carrera (
            id SERIAL PRIMARY KEY,
            iniciada BOOLEAN DEFAULT FALSE,
            hora_inicio TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS corredores (
            id SERIAL PRIMARY KEY,
            dorsal VARCHAR(20) UNIQUE NOT NULL,
            nombre VARCHAR(200) NOT NULL,
            tiempo_llegada TIMESTAMP,
            posicion INTEGER
        )
    """)
    cur.execute("SELECT COUNT(*) FROM carrera")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO carrera (iniciada) VALUES (FALSE)")
    cur.close()
    conn.close()

init_db()

LOGO_IZQ = "/static/BURROTON 2026.png"
LOGO_DER = "/static/LOGO SAN BENITO JOSE.jpg"

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Maratón San Benito José</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
.container { max-width: 960px; margin: 0 auto; background: #fff; border-radius: 16px; padding: 28px; box-shadow: 0 20px 60px rgba(0,0,0,.15); }
.header { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.header img { height: 70px; width: auto; object-fit: contain; }
.header h1 { font-size: 1.6rem; color: #1e293b; text-align: center; flex: 1; }
.barra { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.barra button, .barra input { padding: 10px 16px; font-size: .95rem; border-radius: 8px; border: 1px solid #d1d5db; outline: none; }
.barra input:focus { border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,.15); }
.barra button { background: #6366f1; color: #fff; border: none; cursor: pointer; font-weight: 600; transition: background .15s; }
.barra button:hover { background: #4f46e5; }
.barra button.verde { background: #10b981; }
.barra button.verde:hover { background: #059669; }
.barra button.rojo { background: #ef4444; }
.barra button.rojo:hover { background: #dc2626; }
.barra input { flex: 1; min-width: 100px; }
.estado { padding: 10px 18px; border-radius: 8px; margin-bottom: 16px; font-weight: 700; display: inline-block; font-size: .95rem; }
.estado.parada { background: #fef3c7; color: #92400e; }
.estado.andando { background: #d1fae5; color: #065f46; }
.separador { height: 1px; background: #e5e7eb; margin: 16px 0; }
.buscar-wrap { margin-bottom: 12px; }
.buscar-wrap input { width: 100%; padding: 10px 16px; font-size: .95rem; border-radius: 8px; border: 1px solid #d1d5db; outline: none; }
.buscar-wrap input:focus { border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,.15); }
table { width: 100%; border-collapse: collapse; font-size: .9rem; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
th { background: #f1f5f9; font-weight: 700; color: #475569; position: sticky; top: 0; }
tr:hover { background: #f8fafc; }
.tabla-wrap { max-height: 500px; overflow-y: auto; border-radius: 8px; border: 1px solid #e5e7eb; }
.contador { font-size: .85rem; color: #64748b; margin-bottom: 8px; }
</style>
</head>
<body>
<div class="container" id="app">
  <div class="header">
    <img src=""" + '"{{ logo_izq }}"' + """ alt="Logo">
    <h1>🏃 Maratón San Benito José</h1>
    <img src=""" + '"{{ logo_der }}"' + """ alt="Logo">
  </div>
  <div id="estado-carrera" class="estado parada">⏸ Carrera no iniciada</div>
  <div class="barra">
    <input id="dorsal-input" placeholder="Dorsal" size="6">
    <input id="nombre-input" placeholder="Nombre del corredor">
    <button onclick="registrar()">Registrar</button>
    <button id="btn-iniciar" class="verde" onclick="iniciar()">Iniciar carrera</button>
  </div>
  <div class="barra">
    <input id="llegada-input" placeholder="Dorsal del que llega">
    <button class="verde" onclick="llegada()">Registrar llegada</button>
    <button onclick="resultados()">Ver resultados</button>
  </div>
  <div class="separador"></div>
  <div class="buscar-wrap">
    <input id="buscar-input" placeholder="🔍 Buscar por dorsal o nombre..." oninput="cargar()">
  </div>
  <div class="contador" id="contador"></div>
  <div class="tabla-wrap">
    <table>
      <thead><tr><th>Dorsal</th><th>Nombre</th><th>Llegada</th><th>Posición</th></tr></thead>
      <tbody id="tabla"></tbody>
    </table>
  </div>
</div>
<script>
function cargar() {
  const q = document.getElementById('buscar-input').value.trim();
  const url = q ? '/api/buscar?q=' + encodeURIComponent(q) : '/api/datos';
  fetch(url).then(r=>r.json()).then(d=>{
    const tbody = document.getElementById('tabla');
    tbody.innerHTML = '';
    (d.corredores||[]).forEach(c => {
      const tr = document.createElement('tr');
      const llegada = c.tiempo_llegada || '\u2014';
      const pos = c.posicion ? '#' + c.posicion : '\u2014';
      tr.innerHTML = '<td>' + c.dorsal + '</td><td>' + c.nombre + '</td><td>' + llegada + '</td><td>' + pos + '</td>';
      tbody.appendChild(tr);
    });
    document.getElementById('contador').textContent = 'Total: ' + (d.corredores||[]).length + ' corredores';
    const est = document.getElementById('estado-carrera');
    if (d.carrera_iniciada) {
      est.textContent = '\uD83C\uDFC1 Carrera en curso \u2014 Salida: ' + d.hora_inicio;
      est.className = 'estado andando';
      document.getElementById('btn-iniciar').disabled = true;
    } else {
      est.textContent = '\u23F8 Carrera no iniciada';
      est.className = 'estado parada';
      document.getElementById('btn-iniciar').disabled = false;
    }
  });
}
function registrar() {
  const dorsal = document.getElementById('dorsal-input').value.trim();
  const nombre = document.getElementById('nombre-input').value.trim();
  if (!dorsal || !nombre) return alert('Completa dorsal y nombre.');
  fetch('/api/registrar', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({dorsal, nombre}) })
    .then(r=>r.json()).then(d=> { if(d.error) alert(d.error); else { document.getElementById('dorsal-input').value=''; document.getElementById('nombre-input').value=''; cargar(); } });
}
function iniciar() {
  fetch('/api/iniciar', {method:'POST'}).then(r=>r.json()).then(d=> { if(d.error) alert(d.error); else cargar(); });
}
function llegada() {
  const dorsal = document.getElementById('llegada-input').value.trim();
  if (!dorsal) return alert('Ingresa un dorsal.');
  fetch('/api/llegada', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({dorsal})})
    .then(r=>r.json()).then(d=> { if(d.error) alert(d.error); else { document.getElementById('llegada-input').value=''; cargar(); if(d.mensaje) alert(d.mensaje); } });
}
function resultados() {
  fetch('/api/resultados').then(r=>r.json()).then(d=> {
    if(d.error) return alert(d.error);
    let txt = 'RESULTADOS\\n' + '='.repeat(30) + '\\n';
    d.llegados.forEach(c => { txt += '#' + c.pos + '  ' + c.dorsal + '  ' + c.nombre + '  ' + c.tiempo + '\\n'; });
    alert(txt);
  });
}
cargar();
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML, logo_izq=LOGO_IZQ, logo_der=LOGO_DER)

def get_carrera(cur):
    cur.execute("SELECT iniciada, hora_inicio FROM carrera WHERE id = 1")
    row = cur.fetchone()
    return {"carrera_iniciada": row[0], "hora_inicio": row[1].isoformat() if row[1] else None}

@app.route("/api/datos")
def api_datos():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT dorsal, nombre, tiempo_llegada, posicion FROM corredores ORDER BY id")
    corredores = []
    for r in cur.fetchall():
        corredores.append({
            "dorsal": r["dorsal"],
            "nombre": r["nombre"],
            "tiempo_llegada": r["tiempo_llegada"].isoformat() if r["tiempo_llegada"] else None,
            "posicion": r["posicion"]
        })
    carrera = get_carrera(cur)
    cur.close()
    conn.close()
    return jsonify(carrera_iniciada=carrera["carrera_iniciada"], hora_inicio=carrera["hora_inicio"], corredores=corredores)

@app.route("/api/buscar")
def api_buscar():
    q = request.args.get("q", "").strip()
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT dorsal, nombre, tiempo_llegada, posicion FROM corredores WHERE dorsal ILIKE %s OR nombre ILIKE %s ORDER BY id", (f"%{q}%", f"%{q}%"))
    corredores = []
    for r in cur.fetchall():
        corredores.append({
            "dorsal": r["dorsal"],
            "nombre": r["nombre"],
            "tiempo_llegada": r["tiempo_llegada"].isoformat() if r["tiempo_llegada"] else None,
            "posicion": r["posicion"]
        })
    carrera = get_carrera(cur)
    cur.close()
    conn.close()
    return jsonify(carrera_iniciada=carrera["carrera_iniciada"], hora_inicio=carrera["hora_inicio"], corredores=corredores)

@app.route("/api/registrar", methods=["POST"])
def api_registrar():
    dorsal = request.json.get("dorsal", "").strip()
    nombre = request.json.get("nombre", "").strip()
    if not dorsal or not nombre:
        return jsonify(error="Completa todos los campos."), 400
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO corredores (dorsal, nombre) VALUES (%s, %s)", (dorsal, nombre))
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify(error="Ya existe un corredor con ese dorsal."), 400
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(ok=True)

@app.route("/api/iniciar", methods=["POST"])
def api_iniciar():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT iniciada FROM carrera WHERE id = 1")
    if cur.fetchone()[0]:
        cur.close()
        conn.close()
        return jsonify(error="La carrera ya está iniciada."), 400
    ahora = datetime.now()
    cur.execute("UPDATE carrera SET iniciada = TRUE, hora_inicio = %s WHERE id = 1", (ahora,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(ok=True)

@app.route("/api/llegada", methods=["POST"])
def api_llegada():
    dorsal = request.json.get("dorsal", "").strip()
    conn = get_db()
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
        return jsonify(error="Dorsal no encontrado."), 404
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
    return jsonify(ok=True, mensaje=f"\u00a1{row[1]} lleg\u00f3! #{posicion} \u2014 {h}h {m}m {s}s")

@app.route("/api/resultados")
def api_resultados():
    conn = get_db()
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
        return jsonify(error="A\u00fan no hay llegadas."), 400
    res = []
    for r in rows:
        trans = r[3] - inicio
        h, resto = divmod(int(trans.total_seconds()), 3600)
        m, s = divmod(resto, 60)
        res.append({"pos": r[2], "dorsal": r[0], "nombre": r[1], "tiempo": f"{h}h {m}m {s}s"})
    cur.close()
    conn.close()
    return jsonify(llegados=res)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
