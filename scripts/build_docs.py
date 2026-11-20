#!/usr/bin/env python3
"""Genera la landing estática de GitHub Pages a partir del motor de Markov."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app.markov import default_scenario, format_probability  # noqa: E402

DOCS = RAIZ / "docs"
VENDOR = RAIZ / "app" / "static" / "vendor" / "chart.umd.min.js"
RENDER_URL = os.environ.get(
    "RENDER_URL", "https://matrizmarkov-eragon1020.onrender.com"
)
REPO_URL = "https://github.com/eragon1020/Matrizmarkov"

ESTILOS = """
:root{--bg:#f4f6fb;--surface:#fff;--ink:#111827;--muted:#5b6475;--line:#e2e8f0;
--primary:#4f46e5;--primary-dark:#3730a3;--soft:#eef2ff;--accent:#0ea5e9}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 10% -10%,rgba(79,70,229,.16),transparent 42%),
radial-gradient(circle at 95% 0%,rgba(14,165,233,.14),transparent 38%),var(--bg);color:var(--ink);
font-family:"Segoe UI",system-ui,-apple-system,Arial,sans-serif;line-height:1.55}
a{color:var(--primary)}h1,h2,h3,h4{margin:0;line-height:1.2;letter-spacing:-.02em}p{margin:0}
.wrap{width:min(1180px,94vw);margin:0 auto;padding:0 0 48px}
header{background:rgba(17,24,39,.96);color:#f8fafc;padding:16px 0;margin-bottom:24px}
header .wrap{display:flex;align-items:center;justify-content:space-between;gap:20px;padding-bottom:0}
.brand{display:flex;align-items:center;gap:12px}.mark{display:grid;place-items:center;width:42px;height:42px;
border-radius:12px;background:linear-gradient(135deg,var(--primary),var(--accent));font-weight:800;color:#fff}
.brand h1{font-size:1.1rem}.brand p{font-size:.8rem;color:#cbd5e1}
nav{display:flex;gap:16px}nav a{color:#e2e8f0;text-decoration:none;font-weight:600;font-size:.9rem}
.hero{padding:30px;border-radius:18px;background:linear-gradient(120deg,#111827,#312e81 58%,#0e7490);
color:#f8fafc;box-shadow:0 14px 34px rgba(15,23,42,.14);display:flex;justify-content:space-between;
align-items:center;gap:24px;margin-bottom:20px}.hero h2{font-size:clamp(1.5rem,3vw,2.2rem);margin:6px 0 10px}
.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:.72rem;font-weight:700;color:#a5b4fc}
.hero p{max-width:720px;color:#dbeafe;font-size:.95rem}
.formula{padding:16px 22px;border:1px solid rgba(255,255,255,.22);border-radius:14px;
background:rgba(255,255,255,.08);font-size:1.3rem;font-weight:700;white-space:nowrap}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0 24px}
.btn{display:inline-block;padding:11px 20px;border-radius:11px;text-decoration:none;font-weight:700;font-size:.9rem}
.btn-primary{background:var(--primary);color:#fff;box-shadow:0 8px 18px rgba(79,70,229,.3)}
.btn-secondary{background:#fff;border:1px solid var(--line);color:var(--ink)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:22px;
box-shadow:0 12px 30px rgba(15,23,42,.08);margin-bottom:18px}.card h3{font-size:1.1rem;margin-bottom:14px}
.card h4{font-size:.95rem;margin:20px 0 10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
table{border-collapse:collapse;width:100%;font-size:.86rem}th,td{padding:8px 10px;text-align:center;
border-bottom:1px solid var(--line)}thead th{background:#f8fafc;color:var(--muted);font-size:.74rem;
text-transform:uppercase;letter-spacing:.05em}tbody th{text-align:left}
.scroll{overflow-x:auto}.heatmap td{font-weight:700;font-size:.78rem}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:16px}
.stat{padding:14px;border-radius:12px;background:var(--soft);border:1px solid #e0e7ff}
.stat span{display:block;font-size:.78rem;font-weight:700;color:var(--primary-dark)}
.stat strong{font-size:1.5rem}.stat small{color:var(--muted);font-size:.7rem}
.chart{position:relative;height:250px;border:1px solid var(--line);border-radius:12px;padding:10px;
background:#f8fafc}.chart h4{margin:0 0 8px}
.hint{color:var(--muted);font-size:.84rem}.note{padding:12px 16px;border-radius:12px;background:#fffbeb;
border:1px solid #fde68a;color:#92400e;font-size:.86rem;margin:16px 0}
footer{text-align:center;color:var(--muted);font-size:.82rem;padding:22px}
@media(max-width:760px){.hero{flex-direction:column;align-items:flex-start}header .wrap{flex-direction:column;align-items:flex-start}}
"""


def _tabla_matriz(resultado: dict) -> str:
    estados = resultado["estados"]
    encabezado = "".join(f"<th>{estado}</th>" for estado in estados)
    filas = []
    for i, fila in enumerate(resultado["matriz"]):
        celdas = "".join(f"<td>{format_probability(v)}</td>" for v in fila)
        filas.append(f"<tr><th>{estados[i]}</th>{celdas}</tr>")
    return (
        '<div class="scroll"><table><thead><tr><th>Desde \\ Hacia</th>'
        f"{encabezado}</tr></thead><tbody>{''.join(filas)}</tbody></table></div>"
    )


def _tabla_resultados(resultado: dict) -> str:
    estados = resultado["estados"]
    encabezado = "".join(f"<th>{estado}</th>" for estado in estados)
    filas = []
    for item in resultado["resultados"]:
        celdas = "".join(
            f"<td>{format_probability(v)}</td>" for v in item["probabilidades"]
        )
        etiqueta = (
            f"{item['paso']} <span style='font-size:.66rem;color:#0369a1'>personalizado</span>"
            if item["personalizado"]
            else str(item["paso"])
        )
        filas.append(f"<tr><td>{etiqueta}</td>{celdas}</tr>")
    celdas_est = "".join(
        f"<td>{format_probability(v)}</td>" for v in resultado["estacionaria"]
    )
    filas.append(
        '<tr style="background:#ecfdf5;font-weight:700;color:#065f46">'
        f"<td>Estacionaria</td>{celdas_est}</tr>"
    )
    return (
        '<div class="scroll"><table><thead><tr><th>Paso</th>'
        f"{encabezado}</tr></thead><tbody>{''.join(filas)}</tbody></table></div>"
    )


def _heatmap(resultado: dict) -> str:
    estados = resultado["estados"]
    encabezado = "".join(f"<th>{estado}</th>" for estado in estados)
    filas = []
    for i, fila in enumerate(resultado["matriz"]):
        celdas = []
        for valor in fila:
            color = "#ffffff" if valor > 0.45 else "#1f2937"
            celdas.append(
                f'<td style="background:rgba(79,70,229,{valor});color:{color}">'
                f"{format_probability(valor)}</td>"
            )
        filas.append(f"<tr><th>{estados[i]}</th>{''.join(celdas)}</tr>")
    return (
        '<div class="scroll"><table class="heatmap"><thead><tr><th></th>'
        f"{encabezado}</tr></thead><tbody>{''.join(filas)}</tbody></table></div>"
    )


def _stats(resultado: dict) -> str:
    return "".join(
        f'<div class="stat"><span>{estado}</span><strong>{format_probability(valor)}</strong>'
        "<small>probabilidad estacionaria</small></div>"
        for estado, valor in zip(resultado["estados"], resultado["estacionaria"])
    )


def construir_html(resultado: dict) -> str:
    datos = json.dumps(resultado, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Cadena de Markov aplicada a una sesión de gaming: resultados, gráficas y distribución estacionaria.">
<title>Cadenas de Markov · Sesión de gaming</title>
<style>{ESTILOS}</style>
</head>
<body>
<header>
  <div class="wrap">
    <div class="brand">
      <span class="mark">M</span>
      <div><h1>Cadenas de Markov</h1><p>Sesión de gaming · predicción de estados</p></div>
    </div>
    <nav>
      <a href="{REPO_URL}">GitHub</a>
      <a href="{RENDER_URL}">App en Render</a>
    </nav>
  </div>
</header>
<div class="wrap">
  <section class="hero">
    <div>
      <p class="eyebrow">Modelo de Markov · 3 estados</p>
      <h2>¿Cuánto tiempo seguirás jugando?</h2>
      <p>Esta demo calcula la evolución de una sesión de gaming con estados
      <strong>Jugando</strong>, <strong>En pausa</strong> y <strong>Descansando</strong>.
      Cada paso representa 10 minutos. Los resultados se generan con el mismo motor
      Python que usa la aplicación interactiva.</p>
    </div>
    <div class="formula">π<sub>n</sub> = π<sub>0</sub> · P<sup>n</sup></div>
  </section>

  <div class="actions">
    <a class="btn btn-primary" href="{RENDER_URL}">Abrir aplicación interactiva</a>
    <a class="btn btn-secondary" href="{REPO_URL}">Ver código y especificaciones</a>
  </div>

  <div class="note">
    GitHub Pages solo aloja esta demo estática. Para editar la matriz y guardar
    escenarios, abre la aplicación Flask desplegada en Render o ejecútala en local
    con <code>flask --app wsgi run --debug</code>.
  </div>

  <section class="card">
    <h3>Vista de la aplicación</h3>
    <img src="captura.png" alt="Captura de la aplicación con la matriz, gráficas y tabla de resultados"
         style="width:100%;border-radius:12px;border:1px solid var(--line)">
  </section>

  <section class="card">
    <h3>Matriz de transición</h3>
    {_tabla_matriz(resultado)}
    <h4>Mapa de calor</h4>
    {_heatmap(resultado)}
  </section>

  <section class="card">
    <h3>Distribución estacionaria</h3>
    <div class="stats">{_stats(resultado)}</div>
    <p class="hint">A largo plazo, el jugador reparte su tiempo según estos porcentajes.</p>
  </section>

  <section class="card">
    <h3>Resultados por paso</h3>
    {_tabla_resultados(resultado)}
  </section>

  <section class="card">
    <h3>Gráficas</h3>
    <div class="grid">
      <div class="chart"><h4>Evolución por paso</h4><canvas id="lineas"></canvas></div>
      <div class="chart"><h4>Comparación por paso</h4><canvas id="barras"></canvas></div>
      <div class="chart"><h4>Estacionaria</h4><canvas id="dona"></canvas></div>
    </div>
  </section>

  <section class="card">
    <h3>¿Cómo se calcula?</h3>
    <p class="hint">Se multiplica la distribución inicial por la matriz de transición
    elevada al número de pasos: π<sub>n</sub> = π<sub>0</sub> · P<sup>n</sup>.
    La distribución estacionaria satisface πP = π y suma 1. Los pasos requeridos son
    1, 3, 5 y 10; la aplicación permite añadir pasos personalizados.</p>
  </section>
</div>
<footer>
  Proyecto académico de Cadenas de Markov, SDD y OpenSpec · Generado con Python
</footer>
<script src="chart.umd.min.js"></script>
<script>
const datos = {datos};
const colores = ["#4f46e5", "#0ea5e9", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"];
const base = {{
  responsive: true, maintainAspectRatio: false, animation: false,
  plugins: {{ legend: {{ position: "bottom", labels: {{ boxWidth: 12, font: {{ size: 10 }} }} }} }},
  scales: {{ y: {{ beginAtZero: true, max: 1 }} }}
}};
new Chart(document.getElementById("lineas"), {{
  type: "line",
  data: {{
    labels: [0].concat(datos.resultados.map(r => r.paso)),
    datasets: datos.estados.map((e, i) => ({{
      label: e,
      data: [datos.distribucion_inicial[i]].concat(datos.resultados.map(r => r.probabilidades[i])),
      borderColor: colores[i], backgroundColor: colores[i] + "33",
      tension: .3, borderWidth: 2, pointRadius: 4
    }}))
  }},
  options: base
}});
new Chart(document.getElementById("barras"), {{
  type: "bar",
  data: {{
    labels: datos.resultados.map(r => "Paso " + r.paso),
    datasets: datos.estados.map((e, i) => ({{
      label: e,
      data: datos.resultados.map(r => r.probabilidades[i]),
      backgroundColor: colores[i], borderRadius: 6
    }}))
  }},
  options: base
}});
new Chart(document.getElementById("dona"), {{
  type: "doughnut",
  data: {{
    labels: datos.estados,
    datasets: [{{ data: datos.estacionaria,
      backgroundColor: datos.estados.map((_, i) => colores[i]), borderWidth: 2,
      borderColor: "#fff" }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false, animation: false,
    plugins: {{ legend: {{ position: "bottom" }} }} }}
}});
</script>
</body>
</html>
"""


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    resultado = default_scenario()
    (DOCS / "index.html").write_text(construir_html(resultado), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    if VENDOR.exists():
        shutil.copy2(VENDOR, DOCS / "chart.umd.min.js")
    print(f"Landing generada en {DOCS / 'index.html'}")


if __name__ == "__main__":
    main()
