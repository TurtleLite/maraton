import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Buscador de Redes Sociales</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', -apple-system, sans-serif; background: #f0f4f8; color: #1a2a3a; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
.card { width: 100%; max-width: 900px; background: #fff; border-radius: 20px; padding: 36px 40px; box-shadow: 0 4px 24px rgba(0,0,0,.06); animation: fadeUp .5s ease-out; }
h1 { font-size: 1.8rem; font-weight: 800; color: #1a2a3a; margin-bottom: 4px; }
.sub { color: #5a7a9a; font-size: .9rem; margin-bottom: 24px; }
textarea { width: 100%; padding: 14px 18px; font-size: .9rem; border-radius: 12px; border: 1px solid #d0dce8; outline: none; font-family: inherit; background: #f7faff; resize: vertical; min-height: 100px; transition: all .2s ease; color: #1a2a3a; }
textarea:focus { border-color: #4a7fc8; box-shadow: 0 0 0 3px rgba(74,127,200,.18); background: #fff; }
.btn-row { display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap; align-items: center; }
button { padding: 10px 24px; font-size: .875rem; border-radius: 10px; border: none; font-weight: 600; cursor: pointer; font-family: inherit; transition: all .2s ease; }
.btn-buscar { background: #4a7fc8; color: #fff; }
.btn-buscar:hover { background: #3a6ab0; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(74,127,200,.35); }
.btn-buscar:disabled { opacity: .5; cursor: not-allowed; transform: none; box-shadow: none; }
.btn-ejemplo { background: #e8f0fe; color: #2c5f8a; }
.btn-ejemplo:hover { background: #d6e4f5; }
.loading { display: none; align-items: center; gap: 8px; color: #5a7a9a; font-size: .85rem; margin-top: 8px; }
.loading.show { display: flex; }
.spinner { width: 16px; height: 16px; border: 2px solid #d0dce8; border-top-color: #4a7fc8; border-radius: 50%; animation: spin .6s linear infinite; }
.resultados { margin-top: 20px; display: none; }
.resultados.show { display: block; }
.resumen { font-size: .85rem; color: #5a7a9a; margin-bottom: 14px; }
table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: .85rem; }
th, td { padding: 11px 14px; text-align: left; border-bottom: 1px solid #dce6f0; }
th { background: #eef4fa; font-weight: 700; color: #2c5f8a; font-size: .8rem; text-transform: uppercase; letter-spacing: .04em; }
th:first-child { border-radius: 10px 0 0 0; }
th:last-child { border-radius: 0 10px 0 0; }
tr:last-child td:first-child { border-radius: 0 0 0 10px; }
tr:last-child td:last-child { border-radius: 0 0 10px 0; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #f0f6fc; }
.encontrado { color: #2a7a48; font-weight: 600; }
.no-encontrado { color: #b05046; }
.sin-verificar { color: #8a9ab0; }
a { color: #4a7fc8; text-decoration: none; font-weight: 500; }
a:hover { text-decoration: underline; }
.red-icon { width: 20px; height: 20px; display: inline-block; vertical-align: middle; margin-right: 4px; }
.nombre-usuario { font-weight: 600; color: #1a2a3a; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="card">
  <h1>🔍 Buscador de Redes Sociales</h1>
  <p class="sub">Ingresa uno o más nombres de usuario para buscar en Facebook, Instagram y TikTok</p>
  <textarea id="input-nombres" placeholder="Ej:&#10;turtlelite&#10;openai&#10;github"></textarea>
  <div class="btn-row">
    <button class="btn-buscar" onclick="buscar()">Buscar</button>
    <button class="btn-ejemplo" onclick="ponerEjemplo()">Cargar ejemplos</button>
  </div>
  <div class="loading" id="loading"><div class="spinner"></div> Buscando perfiles...</div>
  <div class="resultados" id="resultados">
    <div class="resumen" id="resumen"></div>
    <div id="tabla-wrap"></div>
  </div>
</div>
<script>
function ponerEjemplo() {
  document.getElementById('input-nombres').value = 'turtlelite\\nopenai\\ngithub';
}
function buscar() {
  const raw = document.getElementById('input-nombres').value.trim();
  if (!raw) return;
  const nombres = raw.split(/[\\n,]+/).map(s => s.trim()).filter(Boolean);
  if (!nombres.length) return;
  document.getElementById('loading').classList.add('show');
  document.getElementById('resultados').classList.remove('show');
  const btn = document.querySelector('.btn-buscar');
  btn.disabled = true;
  fetch('/api/buscar', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({nombres}) })
    .then(r => r.json())
    .then(d => {
      let html = '<table><thead><tr><th>Usuario</th><th>Facebook</th><th>Instagram</th><th>TikTok</th></tr></thead><tbody>';
      d.resultados.forEach(r => {
        html += '<tr><td class="nombre-usuario">' + r.nombre + '</td>';
        ['facebook','instagram','tiktok'].forEach(red => {
          const p = r[red];
          if (p.error) {
            html += '<td class="no-encontrado">' + p.error + '</td>';
          } else {
            const estado = p.existe ? 'encontrado' : (p.verificado === false ? 'no-encontrado' : 'sin-verificar');
            const texto = p.existe ? '✓' : (p.verificado === false ? '✗' : '—');
            html += '<td class="' + estado + '">' + texto + ' <a href="' + p.url + '" target="_blank">' + p.url.split('/').pop() + '</a></td>';
          }
        });
        html += '</tr>';
      });
      html += '</tbody></table>';
      document.getElementById('tabla-wrap').innerHTML = html;
      const total = d.resultados.length;
      const encontrados = d.resultados.filter(r => r.instagram && r.instagram.existe).length;
      document.getElementById('resumen').textContent = total + ' usuario' + (total !== 1 ? 's' : '') + ' — ' + encontrados + ' perfil' + (encontrados !== 1 ? 'es' : '') + ' encontrado' + (encontrados !== 1 ? 's' : '') + ' en Instagram';
      document.getElementById('resultados').classList.add('show');
    })
    .catch(e => alert('Error: ' + e.message))
    .finally(() => { document.getElementById('loading').classList.remove('show'); btn.disabled = false; });
}
</script>
</body>
</html>"""

REDES = [
    {"id": "facebook", "nombre": "Facebook", "url": "https://www.facebook.com/{}"},
    {"id": "instagram", "nombre": "Instagram", "url": "https://www.instagram.com/{}/"},
    {"id": "tiktok", "nombre": "TikTok", "url": "https://www.tiktok.com/@{}"},
]

def verificar_instagram(usuario):
    try:
        r = requests.get(f"https://www.instagram.com/{usuario}/", timeout=8,
                         headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                         allow_redirects=True)
        if r.status_code == 200 and "The link you followed may be broken" not in r.text and "Page Not Found" not in r.text:
            return {"existe": True, "verificado": True}
        return {"existe": False, "verificado": True}
    except:
        return {"existe": False, "verificado": False}

def verificar_facebook(usuario):
    return {"existe": False, "verificado": False}

def verificar_tiktok(usuario):
    return {"existe": False, "verificado": False}

VERIFICADORES = {
    "facebook": verificar_facebook,
    "instagram": verificar_instagram,
    "tiktok": verificar_tiktok,
}

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/buscar", methods=["POST"])
def api_buscar():
    data = request.get_json()
    nombres = data.get("nombres", [])
    resultados = []
    for nombre in nombres:
        nombre = nombre.strip()
        if not nombre:
            continue
        res = {"nombre": nombre}
        for red in REDES:
            url = red["url"].format(nombre)
            try:
                info = VERIFICADORES[red["id"]](nombre)
                res[red["id"]] = {"url": url, **info}
            except Exception as e:
                res[red["id"]] = {"url": url, "error": str(e), "existe": False, "verificado": False}
        resultados.append(res)
    return jsonify(resultados=resultados)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
