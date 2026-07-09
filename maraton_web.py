
import psycopg2
import psycopg2.extras
import json
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

DB_URL = os.environ.get("DATABASE_URL", "postgresql://maraton_db_yu80_user:PGKNIB3F5HTynSqz7Vx6x01vJcQVG3bD@dpg-d97vq9qabeoc739aqnmg-a.virginia-postgres.render.com/maraton_db_yu80?sslmode=require")
app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Maratón</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; background: #f5f5f5; padding: 20px; }
.container { max-width: 800px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,.1); }
h1 { font-size: 1.5rem; margin-bottom: 16px; }
.barra { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.barra button, .barra input { padding: 8px 14px; font-size: .95rem; border-radius: 6px; border: 1px solid #ccc; }
.barra button { background: #2563eb; color: #fff; border: none; cursor: pointer; }
.barra button:hover { background: #1d4ed8; }
.barra button.verde { background: #16a34a; }
.barra button.verde:hover { background: #15803d; }
.barra button.rojo { background: #dc2626; }
.barra button.rojo:hover { background: #b91c1c; }
.barra input { flex: 1; min-width: 120px; }
.estado { padding: 8px 14px; border-radius: 6px; margin-bottom: 16px; font-weight: 600; display: inline-block; }
.estado.parada { background: #fef3c7; color: #92400e; }
.estado.andando { background: #dcfce7; color: #166534; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
th { background: #f9fafb; font-weight: 600; color: #374151; }
tr:hover { background: #f9fafb; }
.medal { font-weight: 700; }
.medal-1 { color: #b8860b; } .medal-2 { color: #a0a0a0; } .medal-3 { color: #cd7f32; }
</style>
</head>
<body>
<div class="container" id="app">
  <h1>🏃 Maratón</h1>
  <div id="estado-carrera" class="estado parada">⏸ Carrera no iniciada</div>
  <div class="barra">
    <input id="dorsal-input" placeholder="Dorsal" size="6">
    <input id="nombre-input" placeholder="Nombre">
    <button onclick="registrar()">Registrar</button>
    <button id="btn-iniciar" class="verde" onclick="iniciar()">Iniciar carrera</button>
  </div>
  <div class="barra">
    <input id="llegada-input" placeholder="Dorsal del que llega">
    <button class="verde" onclick="llegada()">Registrar llegada</button>
    <button onclick="resultados()">Ver resultados</button>
  </div>
  <table>
    <thead><tr><th>Dorsal</th><th>Nombre</th><th>Llegada</th><th>Posición</th></tr></thead>
    <tbody id="tabla"></tbody>
  </table>
</div>
<script>
function cargar() {
  fetch('/api/datos').then(r=>r.json()).then(d=>{
    const tbody = document.getElementById('tabla');
    tbody.innerHTML = '';
    d.corredores.forEach(c => {
      const tr = document.createElement('tr');
      const llegada = c.tiempo_llegada || '—';
      const pos = c.posicion ? `#${c.posicion}` : '—';
      tr.innerHTML = `<td>${c.dorsal}</td><td>${c.nombre}</td><td>${llegada}</td><td>${pos}</td>`;
      tbody.appendChild(tr);
    });
    const est = document.getElementById('estado-carrera');
    if (d.carrera_iniciada) {
      est.textContent = '🏁 Carrera en curso — Salida: ' + d.hora_inicio;
      est.className = 'estado andando';
      document.getElementById('btn-iniciar').disabled = true;
    } else {
      est.textContent = '⏸ Carrera no iniciada';
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
    d.llegados.forEach(c => { txt += `#${c.pos}  ${c.dorsal}  ${c.nombre}  ${c.tiempo}\\n`; });
    alert(txt);
  });
}
cargar();
</script>
</body>
</html>"""

def cargar():
    if not os.path.exists(ARCHIVO):
        return {"carrera_iniciada": False, "hora_inicio": None, "corredores": []}
    with open(ARCHIVO, "r") as f:
        return json.load(f)

def guardar(data):
    with open(ARCHIVO, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/datos")
def api_datos():
    return jsonify(cargar())

@app.route("/api/registrar", methods=["POST"])
def api_registrar():
    data = cargar()
    dorsal = request.json.get("dorsal", "").strip()
    nombre = request.json.get("nombre", "").strip()
    if not dorsal or not nombre:
        return jsonify(error="Completa todos los campos."), 400
    if any(c["dorsal"] == dorsal for c in data["corredores"]):
        return jsonify(error="Ya existe un corredor con ese dorsal."), 400
    data["corredores"].append({"dorsal": dorsal, "nombre": nombre, "tiempo_llegada": None, "posicion": None})
    guardar(data)
    return jsonify(ok=True)

@app.route("/api/iniciar", methods=["POST"])
def api_iniciar():
    data = cargar()
    if data["carrera_iniciada"]:
        return jsonify(error="La carrera ya está iniciada."), 400
    data["carrera_iniciada"] = True
    data["hora_inicio"] = datetime.now().isoformat()
    guardar(data)
    return jsonify(ok=True)

@app.route("/api/llegada", methods=["POST"])
def api_llegada():
    data = cargar()
    if not data["carrera_iniciada"]:
        return jsonify(error="La carrera no ha iniciado."), 400
    dorsal = request.json.get("dorsal", "").strip()
    for c in data["corredores"]:
        if c["dorsal"] == dorsal:
            if c["tiempo_llegada"]:
                return jsonify(error=f"{c['nombre']} ya llegó."), 400
            ahora = datetime.now()
            c["tiempo_llegada"] = ahora.isoformat()
            llegados = [x for x in data["corredores"] if x["tiempo_llegada"]]
            c["posicion"] = len(llegados)
            inicio = datetime.fromisoformat(data["hora_inicio"])
            trans = ahora - inicio
            h, resto = divmod(int(trans.total_seconds()), 3600)
            m, s = divmod(resto, 60)
            guardar(data)
            return jsonify(ok=True, mensaje=f"¡{c['nombre']} llegó! #{c['posicion']} — {h}h {m}m {s}s")
    return jsonify(error="Dorsal no encontrado."), 404

@app.route("/api/resultados")
def api_resultados():
    data = cargar()
    llegados = [c for c in data["corredores"] if c["tiempo_llegada"]]
    llegados.sort(key=lambda x: x["posicion"])
    if not llegados:
        return jsonify(error="Aún no hay llegadas."), 400
    inicio = datetime.fromisoformat(data["hora_inicio"])
    res = []
    for c in llegados:
        llegada = datetime.fromisoformat(c["tiempo_llegada"])
        trans = llegada - inicio
        h, resto = divmod(int(trans.total_seconds()), 3600)
        m, s = divmod(resto, 60)
        res.append({"pos": c["posicion"], "dorsal": c["dorsal"], "nombre": c["nombre"], "tiempo": f"{h}h {m}m {s}s"})
    return jsonify(llegados=res)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
