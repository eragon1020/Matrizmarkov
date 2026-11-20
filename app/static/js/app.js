(function () {
  "use strict";

  const COLORES = ["#4f46e5", "#0ea5e9", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"];
  const NOMBRES_POR_DEFECTO = [
    "Jugando",
    "En pausa",
    "Descansando",
    "Estado 4",
    "Estado 5",
    "Estado 6",
  ];

  let chartLineas = null;
  let chartBarras = null;
  let chartDona = null;
  let datosIniciales = null;

  function formatear(valor) {
    return Number(valor).toFixed(4);
  }

  function escapeHtml(valor) {
    return String(valor)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function leerDatosIniciales() {
    const nodo = document.getElementById("datos-resultado");
    if (!nodo) return null;
    try {
      return JSON.parse(nodo.textContent);
    } catch (error) {
      return null;
    }
  }

  function mostrarError(mensaje) {
    const alerta = document.getElementById("mensaje-error");
    if (!alerta) return;
    alerta.textContent = mensaje;
    alerta.hidden = false;
    alerta.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function ocultarError() {
    const alerta = document.getElementById("mensaje-error");
    if (!alerta) return;
    alerta.textContent = "";
    alerta.hidden = true;
  }

  function construirPayload() {
    const n = Number(document.getElementById("n_estados").value);
    const estados = [];
    const matriz = [];
    const inicial = [];

    for (let i = 0; i < n; i += 1) {
      const nombre = document.querySelector('[name="e_' + i + '"]');
      estados.push(nombre ? nombre.value.trim() : "");
    }

    for (let i = 0; i < n; i += 1) {
      const fila = [];
      for (let j = 0; j < n; j += 1) {
        const celda = document.querySelector('[name="m_' + i + "_" + j + '"]');
        fila.push(Number(celda ? celda.value : NaN));
      }
      matriz.push(fila);
    }

    for (let i = 0; i < n; i += 1) {
      const valor = document.querySelector('[name="p_' + i + '"]');
      inicial.push(Number(valor ? valor.value : NaN));
    }

    const escenario = document.querySelector('[name="escenario_id"]');
    const escenarioId = escenario && escenario.value ? Number(escenario.value) : null;

    return {
      estados: estados,
      matriz: matriz,
      distribucion_inicial: inicial,
      pasos_personalizados: document.getElementById("pasos_personalizados").value,
      escenario_id: escenarioId,
    };
  }

  function matrizPorDefecto(n) {
    if (n === 3) {
      return [
        [0.7, 0.2, 0.1],
        [0.4, 0.3, 0.3],
        [0.15, 0.15, 0.7],
      ];
    }

    const matriz = [];
    for (let i = 0; i < n; i += 1) {
      const fila = new Array(n).fill(0);
      fila[i] = 0.6;
      const otros = [];
      for (let j = 0; j < n; j += 1) {
        if (j !== i) otros.push(j);
      }
      let restante = 0.4;
      otros.forEach(function (j, indice) {
        const valor =
          indice === otros.length - 1 ? restante : 0.4 / (n - 1);
        fila[j] = valor;
        restante -= valor;
      });
      matriz.push(fila);
    }
    return matriz;
  }

  function reconstruirFormulario(n) {
    const nombresActuales = Array.from(
      document.querySelectorAll("#estados-nombres input")
    ).map(function (input) {
      return input.value.trim();
    });

    const estados = [];
    for (let i = 0; i < n; i += 1) {
      estados.push(nombresActuales[i] || NOMBRES_POR_DEFECTO[i]);
    }

    document.getElementById("estados-nombres").innerHTML = estados
      .map(function (nombre, i) {
        return (
          '<label class="field">Estado ' +
          (i + 1) +
          '<input type="text" name="e_' +
          i +
          '" value="' +
          escapeHtml(nombre) +
          '" maxlength="40" required></label>'
        );
      })
      .join("");

    const matriz = matrizPorDefecto(n);
    const tabla = document.getElementById("tabla-matriz");
    tabla.querySelector("thead").innerHTML =
      "<tr><th>Desde \\ Hacia</th>" +
      estados.map(function (nombre) {
        return "<th>" + escapeHtml(nombre) + "</th>";
      }).join("") +
      "</tr>";

    tabla.querySelector("tbody").innerHTML = matriz
      .map(function (fila, i) {
        const celdas = fila
          .map(function (valor, j) {
            return (
              '<td><input type="number" step="0.01" min="0" max="1" name="m_' +
              i +
              "_" +
              j +
              '" value="' +
              Number(valor).toFixed(2) +
              '" required></td>'
            );
          })
          .join("");
        return "<tr><th>" + escapeHtml(estados[i]) + "</th>" + celdas + "</tr>";
      })
      .join("");

    document.getElementById("inicial-grid").innerHTML = estados
      .map(function (nombre, i) {
        return (
          '<label class="field"><span class="inicial-nombre">' +
          escapeHtml(nombre) +
          '</span><input type="number" step="0.01" min="0" max="1" name="p_' +
          i +
          '" value="' +
          (i === 0 ? "1.00" : "0.00") +
          '" required></label>'
        );
      })
      .join("");
  }

  function actualizarEncabezados() {
    const nombres = Array.from(
      document.querySelectorAll("#estados-nombres input")
    ).map(function (input, indice) {
      return input.value.trim() || NOMBRES_POR_DEFECTO[indice];
    });

    document.querySelectorAll("#tabla-matriz thead th").forEach(function (th, i) {
      if (i > 0) th.textContent = nombres[i - 1];
    });

    document.querySelectorAll("#tabla-matriz tbody tr").forEach(function (fila, i) {
      const th = fila.querySelector("th");
      if (th) th.textContent = nombres[i];
    });

    document.querySelectorAll(".inicial-nombre").forEach(function (span, i) {
      span.textContent = nombres[i];
    });
  }

  function actualizarResumen(resultado) {
    const contenedor = document.getElementById("resumen-estacionaria");
    if (!contenedor) return;
    contenedor.innerHTML = resultado.estados
      .map(function (estado, i) {
        return (
          '<div class="stat"><span>' +
          escapeHtml(estado) +
          "</span><strong>" +
          formatear(resultado.estacionaria[i]) +
          "</strong><small>probabilidad estacionaria</small></div>"
        );
      })
      .join("");
  }

  function actualizarTabla(resultado) {
    const tabla = document.getElementById("tabla-resultados");
    if (!tabla) return;

    tabla.querySelector("thead").innerHTML =
      "<tr><th>Paso</th>" +
      resultado.estados.map(function (estado) {
        return "<th>" + escapeHtml(estado) + "</th>";
      }).join("") +
      "</tr>";

    const filas = resultado.resultados
      .map(function (fila) {
        const celdas = fila.probabilidades
          .map(function (valor) {
            return "<td>" + formatear(valor) + "</td>";
          })
          .join("");
        return (
          "<tr><td>" +
          fila.paso +
          (fila.personalizado ? ' <span class="tag">personalizado</span>' : "") +
          "</td>" +
          celdas +
          "</tr>"
        );
      })
      .join("");

    const estacionaria =
      '<tr class="fila-estacionaria"><td>Estacionaria</td>' +
      resultado.estacionaria
        .map(function (valor) {
          return "<td>" + formatear(valor) + "</td>";
        })
        .join("") +
      "</tr>";

    tabla.querySelector("tbody").innerHTML = filas + estacionaria;
  }

  function actualizarPasoAPaso(resultado) {
    const contenedor = document.getElementById("paso-a-paso");
    if (!contenedor) return;

    contenedor.innerHTML = resultado.resultados
      .map(function (fila, indice) {
        const vector = fila.probabilidades.map(formatear).join(", ");
        const matriz = fila.matriz
          .map(function (renglon) {
            return (
              "<tr>" +
              renglon
                .map(function (valor) {
                  return "<td>" + formatear(valor) + "</td>";
                })
                .join("") +
              "</tr>"
            );
          })
          .join("");

        return (
          "<details " +
          (indice === 0 ? "open" : "") +
          "><summary>Paso " +
          fila.paso +
          "</summary><p>π<sub>" +
          fila.paso +
          "</sub> = [" +
          vector +
          ']</p><div class="tabla-scroll"><table class="matriz-paso"><tbody>' +
          matriz +
          "</tbody></table></div></details>"
        );
      })
      .join("");
  }

  function actualizarMapaCalor(resultado) {
    const contenedor = document.getElementById("mapa-calor");
    if (!contenedor) return;

    let html =
      '<table class="heatmap"><thead><tr><th></th>' +
      resultado.estados
        .map(function (estado) {
          return "<th>" + escapeHtml(estado) + "</th>";
        })
        .join("") +
      "</tr></thead><tbody>";

    resultado.matriz.forEach(function (fila, i) {
      html += "<tr><th>" + escapeHtml(resultado.estados[i]) + "</th>";
      fila.forEach(function (valor) {
        const alpha = Math.max(0.06, Math.min(1, Number(valor)));
        const color = alpha > 0.45 ? "#ffffff" : "#1f2937";
        html +=
          '<td style="background: rgba(79, 70, 229, ' +
          alpha +
          "); color: " +
          color +
          '">' +
          formatear(valor) +
          "</td>";
      });
      html += "</tr>";
    });

    html += "</tbody></table>";
    contenedor.innerHTML = html;
  }

  function opcionesBase() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 12, font: { size: 10 } },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 1,
          ticks: {
            callback: function (valor) {
              return Number(valor).toFixed(1);
            },
          },
        },
      },
    };
  }

  function actualizarGraficas(resultado) {
    if (typeof Chart === "undefined") return;

    if (chartLineas) chartLineas.destroy();
    if (chartBarras) chartBarras.destroy();
    if (chartDona) chartDona.destroy();

    const etiquetas = [0].concat(
      resultado.resultados.map(function (fila) {
        return fila.paso;
      })
    );

    const lineas = resultado.estados.map(function (estado, indice) {
      return {
        label: estado,
        data: [resultado.distribucion_inicial[indice]].concat(
          resultado.resultados.map(function (fila) {
            return fila.probabilidades[indice];
          })
        ),
        borderColor: COLORES[indice % COLORES.length],
        backgroundColor: COLORES[indice % COLORES.length] + "33",
        pointBackgroundColor: COLORES[indice % COLORES.length],
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 4,
      };
    });

    chartLineas = new Chart(document.getElementById("grafico-lineas"), {
      type: "line",
      data: { labels: etiquetas, datasets: lineas },
      options: opcionesBase(),
    });

    const barras = resultado.estados.map(function (estado, indice) {
      return {
        label: estado,
        data: resultado.resultados.map(function (fila) {
          return fila.probabilidades[indice];
        }),
        backgroundColor: COLORES[indice % COLORES.length],
        borderRadius: 6,
      };
    });

    chartBarras = new Chart(document.getElementById("grafico-barras"), {
      type: "bar",
      data: {
        labels: resultado.resultados.map(function (fila) {
          return "Paso " + fila.paso;
        }),
        datasets: barras,
      },
      options: opcionesBase(),
    });

    chartDona = new Chart(document.getElementById("grafico-dona"), {
      type: "doughnut",
      data: {
        labels: resultado.estados,
        datasets: [
          {
            data: resultado.estacionaria,
            backgroundColor: resultado.estados.map(function (_, indice) {
              return COLORES[indice % COLORES.length];
            }),
            borderWidth: 2,
            borderColor: "#ffffff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 10 } } },
          tooltip: {
            callbacks: {
              label: function (contexto) {
                return contexto.label + ": " + formatear(contexto.parsed);
              },
            },
          },
        },
      },
    });
  }

  function renderHistorial(items) {
    const seccion = document.querySelector(".history");
    if (!seccion) return;

    if (!items || items.length === 0) {
      seccion.innerHTML =
        '<h3>Historial reciente</h3><p class="hint">Todavía no hay cálculos registrados.</p>';
      return;
    }

    const filas = items
      .map(function (item) {
        return (
          "<tr><td>" +
          item.id +
          "</td><td>" +
          escapeHtml(item.escenario_nombre || "Cálculo libre") +
          "</td><td>" +
          item.pasos.join(", ") +
          "</td><td>[" +
          item.estacionaria.map(formatear).join(", ") +
          "]</td><td>" +
          escapeHtml(item.creado_en) +
          "</td></tr>"
        );
      })
      .join("");

    seccion.innerHTML =
      '<h3>Historial reciente</h3><div class="tabla-scroll"><table class="historial"><thead><tr><th>#</th><th>Escenario</th><th>Pasos</th><th>Distribución estacionaria</th><th>Fecha (UTC)</th></tr></thead><tbody>' +
      filas +
      "</tbody></table></div>";
  }

  async function cargarHistorial() {
    try {
      const respuesta = await fetch("/api/historial?limite=10", {
        headers: { Accept: "application/json" },
      });
      const datos = await respuesta.json();
      if (datos.ok) renderHistorial(datos.historial);
    } catch (error) {
      /* el historial es un extra; un fallo de red no debe romper el cálculo */
    }
  }

  function actualizarTodo(resultado) {
    actualizarResumen(resultado);
    actualizarTabla(resultado);
    actualizarPasoAPaso(resultado);
    actualizarMapaCalor(resultado);
    actualizarGraficas(resultado);
  }

  async function calcular(evento) {
    evento.preventDefault();
    ocultarError();

    try {
      const respuesta = await fetch("/api/calcular", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(construirPayload()),
      });
      const datos = await respuesta.json();
      if (!datos.ok) {
        mostrarError(datos.error || "No se pudieron calcular los resultados.");
        return;
      }
      actualizarTodo(datos.resultado);
      await cargarHistorial();
    } catch (error) {
      mostrarError("No se pudo conectar con el servidor.");
    }
  }

  async function guardarEscenario() {
    const nombre = document.getElementById("nombre_escenario").value.trim();
    if (!nombre) {
      mostrarError("Escribe un nombre para guardar el escenario.");
      return;
    }

    const payload = construirPayload();
    try {
      const respuesta = await fetch("/api/escenarios", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          nombre: nombre,
          estados: payload.estados,
          matriz: payload.matriz,
          distribucion_inicial: payload.distribucion_inicial,
        }),
      });
      const datos = await respuesta.json();
      if (!datos.ok) {
        mostrarError(datos.error || "No se pudo guardar el escenario.");
        return;
      }
      window.location = "/?escenario=" + datos.escenario.id;
    } catch (error) {
      mostrarError("No se pudo conectar con el servidor.");
    }
  }

  function iniciar() {
    datosIniciales = leerDatosIniciales();

    const formulario = document.getElementById("form-markov");
    if (formulario) formulario.addEventListener("submit", calcular);

    const selectorEstados = document.getElementById("n_estados");
    if (selectorEstados) {
      selectorEstados.addEventListener("change", function () {
        reconstruirFormulario(Number(selectorEstados.value));
      });
    }

    const contenedorNombres = document.getElementById("estados-nombres");
    if (contenedorNombres) {
      contenedorNombres.addEventListener("input", actualizarEncabezados);
    }

    const botonGuardar = document.getElementById("btn-guardar");
    if (botonGuardar) botonGuardar.addEventListener("click", guardarEscenario);

    if (datosIniciales) {
      actualizarMapaCalor(datosIniciales);
      actualizarGraficas(datosIniciales);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
