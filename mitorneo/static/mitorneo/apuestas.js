document.addEventListener("DOMContentLoaded", function () {
    const recargarSaldoBtn = document.getElementById("recargar-saldo-btn");
    if (recargarSaldoBtn) {
        recargarSaldoBtn.addEventListener("click", function(event) {
            event.preventDefault();
            const modal = document.getElementById("modal-recarga");
            if (modal) {
                modal.style.display = "block";
                crearCamposPago();
            }
        });
    }

    function crearCamposPago() {
        const modalContent = document.querySelector("#modal-recarga .modal-content");
        let camposPagoDiv = document.getElementById("campos-pago");
        if (!camposPagoDiv) {
            camposPagoDiv = document.createElement("div");
            camposPagoDiv.id = "campos-pago";
            camposPagoDiv.style.marginBottom = "1rem";
            modalContent.insertBefore(camposPagoDiv, document.getElementById("btn-confirmar-recarga"));
        }

        const metodoPagoSelect = document.getElementById("metodo-pago");
        if (metodoPagoSelect) {
            metodoPagoSelect.addEventListener("change", mostrarCamposPago);
            mostrarCamposPago();
        }

        function mostrarCamposPago() {
            const metodo = metodoPagoSelect.value;
            camposPagoDiv.innerHTML = "";
            if (metodo === "tarjeta") {
                camposPagoDiv.innerHTML = `
                    <label for="nombre-tarjeta">Nombre en la Tarjeta:</label>
                    <input type="text" id="nombre-tarjeta" placeholder="Nombre completo" style="width: 100%; padding: 0.5rem; border-radius: 4px; border: none; margin-bottom: 0.5rem;" />
                    <label for="numero-tarjeta">Número de Tarjeta:</label>
                    <input type="text" id="numero-tarjeta" placeholder="1234 5678 9012 3456" style="width: 100%; padding: 0.5rem; border-radius: 4px; border: none; margin-bottom: 0.5rem;" />
                    <label for="fecha-expiracion">Fecha de Expiración:</label>
                    <input type="month" id="fecha-expiracion" style="width: 100%; padding: 0.5rem; border-radius: 4px; border: none; margin-bottom: 0.5rem;" />
                    <label for="cvv">CVV:</label>
                    <input type="text" id="cvv" placeholder="123" style="width: 100%; padding: 0.5rem; border-radius: 4px; border: none;" />
                `;
            } else if (metodo === "paypal") {
                camposPagoDiv.innerHTML = `
                    <label for="email-paypal">Email PayPal:</label>
                    <input type="email" id="email-paypal" placeholder="usuario@paypal.com" style="width: 100%; padding: 0.5rem; border-radius: 4px; border: none;" />
                `;
            }
        }
    }

    // Cerrar modal
    const cerrarModalBtn = document.getElementById("cerrar-modal");
    if (cerrarModalBtn) {
        cerrarModalBtn.addEventListener("click", () => {
            const modal = document.getElementById("modal-recarga");
            if (modal) {
                modal.style.display = "none";
            }
        });
    }

    // Confirmar recarga
    const btnConfirmarRecarga = document.getElementById("btn-confirmar-recarga");
    if (btnConfirmarRecarga) {
        btnConfirmarRecarga.addEventListener("click", () => {
            const montoInput = document.getElementById("monto-recarga");
            const metodoPagoSelect = document.getElementById("metodo-pago");
            const monto = parseFloat(montoInput.value);
            const metodo_pago = metodoPagoSelect.value;

            // Recopilar datos de pago según método
            let datos_pago = {};
            if (metodo_pago === "tarjeta") {
                const nombreTarjeta = document.getElementById("nombre-tarjeta").value.trim();
                const numeroTarjeta = document.getElementById("numero-tarjeta").value.trim();
                const fechaExpiracion = document.getElementById("fecha-expiracion").value.trim();
                const cvv = document.getElementById("cvv").value.trim();
                if (!nombreTarjeta || !numeroTarjeta || !fechaExpiracion || !cvv) {
                    alert("Por favor, complete todos los campos de la tarjeta.");
                    return;
                }
                datos_pago = { nombreTarjeta, numeroTarjeta, fechaExpiracion, cvv };
            } else if (metodo_pago === "paypal") {
                const emailPaypal = document.getElementById("email-paypal").value.trim();
                if (!emailPaypal) {
                    alert("Por favor, ingrese el email de PayPal.");
                    return;
                }
                datos_pago = { emailPaypal };
            }

            if (isNaN(monto) || monto <= 0) {
                alert("Cantidad inválida.");
                return;
            }
            fetch("/torneo/api/recargar_saldo/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify({ 
                    monto: monto,
                    metodo_pago: metodo_pago,
                    datos_pago: datos_pago
                })
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text || "Error al recargar saldo."); });
                }
                return response.json();
            })
            .then(data => {
                // --- INICIO DE LA SOLUCIÓN ---

                // 1. Imprimimos en la consola para depurar (esto es útil, lo mantenemos).
                console.log("Respuesta completa de la API:", data);

                // 2. Buscamos el valor del saldo de forma segura.
                // Intentará usar 'data.saldo'. Si es undefined, intentará 'data.nuevo_saldo'.
                const saldoRecibido = data.saldo || data.nuevo_saldo;

                // 3. Verificamos si hemos encontrado un valor válido ANTES de usarlo.
                if (saldoRecibido !== undefined && saldoRecibido !== null) {
                    alert("Saldo recargado correctamente.");
                    actualizarSaldoVisual(saldoRecibido); // ¡Ahora pasamos un valor que sabemos que existe!
                    
                    // Cerramos el modal y limpiamos el input
                    const modal = document.getElementById("modal-recarga");
                    if (modal) {
                        modal.style.display = "none";
                    }
                    if (montoInput) {
                        montoInput.value = "";
                    }
                } else {
                    // Si no encontramos el saldo, informamos al usuario y al desarrollador.
                    alert("Error: La recarga se procesó, pero no se pudo obtener el nuevo saldo. Por favor, recargue la página.");
                    console.error("La respuesta de la API no contenía un campo 'saldo' o 'nuevo_saldo' válido.", data);
                }
                // --- FIN DE LA SOLUCIÓN ---
            })
            .catch(error => {
                alert("Error al procesar la recarga: " + error.message);
            });

    function actualizarSaldoVisual(nuevoSaldo) {
        const saldoUsuario = document.getElementById("saldo-usuario");
        // Esta función ahora es segura porque solo la llamamos si 'nuevoSaldo' tiene un valor.
        if (saldoUsuario && nuevoSaldo !== undefined && nuevoSaldo !== null) {
            saldoUsuario.textContent = parseFloat(nuevoSaldo).toFixed(2);
        }
    }
        });
    }

    const equipoSelect = document.getElementById("equipo-select");
    const partidoSelect = document.getElementById("partido-select");
    const montoInput = document.getElementById("monto-input");
    const apostarBtn = document.getElementById("apostar-btn");
    const apuestasList = document.getElementById("apuestas-list");
    const saldoUsuario = document.getElementById("saldo-usuario");
    const probabilidadVictoriaSpan = document.getElementById("probabilidad-victoria");
    const chartContainer = document.getElementById("grafica-estadisticas");
    const chartCanvas = document.getElementById("chart-estadisticas");
    let chart = null;

    // Función para cargar las apuestas del usuario
    function cargarApuestas() {
        fetch("/torneo/api/apuestas/")
            .then(response => response.json())
            .then(data => {
                apuestasList.innerHTML = "";
                data.forEach(apuesta => {
                    const li = document.createElement("li");
                    li.textContent = `${apuesta.equipo} - Monto: $${apuesta.monto.toFixed(2)} - Fecha: ${new Date(apuesta.fecha_apuesta).toLocaleString()}`;
                    apuestasList.appendChild(li);
                });
            });
    }

    // Función para calcular probabilidad de victoria (simulada)
    function calcularProbabilidad(equipoId) {
        if (!equipoId) {
            probabilidadVictoriaSpan.textContent = "-";
            return;
        }
        // Llamar API para obtener estadísticas reales
        fetch(`/torneo/api/estadisticas_equipo/?equipo_id=${equipoId}`)
            .then(response => response.json())
            .then(data => {
                // Ejemplo: usar victorias y partidos para calcular probabilidad simple
                const totalPartidos = data.victorias + (data.derrotas || 0);
                let prob = 0;
                if (totalPartidos > 0) {
                    prob = (data.victorias / totalPartidos) * 100;
                }
                probabilidadVictoriaSpan.textContent = prob.toFixed(2) + "%";
                mostrarGrafica(data);
            })
            .catch(() => {
                probabilidadVictoriaSpan.textContent = "N/A";
                if (chart) {
                    chart.destroy();
                    chart = null;
                }
            });
    }

    // Función para mostrar gráfica de estadísticas
    function mostrarGrafica(data) {
        if (chart) {
            chart.destroy();
        }
        const labels = ["Victorias", "Derrotas", "Empates"];
        const valores = [
            data.victorias || 0,
            data.derrotas || 0,
            data.empates || 0
        ];
        chart = new Chart(chartCanvas, {
            type: "pie",
            data: {
                labels: labels,
                datasets: [{
                    label: "Estadísticas del equipo",
                    data: valores,
                    backgroundColor: [
                        "rgba(75, 192, 192, 0.6)",
                        "rgba(255, 99, 132, 0.6)",
                        "rgba(255, 206, 86, 0.6)"
                    ],
                    borderColor: [
                        "rgba(75, 192, 192, 1)",
                        "rgba(255, 99, 132, 1)",
                        "rgba(255, 206, 86, 1)"
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        });
    }

    // Evento cambio de equipo para actualizar probabilidad y gráfica
    equipoSelect.addEventListener("change", () => {
        const equipoId = equipoSelect.value;
        calcularProbabilidad(equipoId);
    });

    // Evento click para apostar
    apostarBtn.addEventListener("click", () => {
        const equipoId = equipoSelect.value;
        const partidoId = partidoSelect.value;
        const monto = parseFloat(montoInput.value);

        if (!equipoId) {
            alert("Por favor, selecciona un equipo.");
            return;
        }
        if (!partidoId) {
            alert("Por favor, selecciona un partido.");
            return;
        }
        if (isNaN(monto) || monto <= 0) {
            alert("Por favor, ingresa un monto válido.");
            return;
        }

        fetch("/torneo/api/apuestas/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({
                equipo_id: equipoId,
                partido_id: partidoId,
                monto: monto
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Error al realizar la apuesta.");
            }
            return response.json();
        })
        .then(data => {
            alert("Apuesta realizada con éxito.");
            montoInput.value = "";
            cargarApuestas();
            actualizarSaldo();
        })
        .catch(error => {
            alert(error.message);
        });
    });

    // Función para obtener cookie CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Función para actualizar saldo mostrado
    function actualizarSaldo() {
        fetch("/torneo/api/saldo/")
            .then(response => response.json())
            .then(data => {
                saldoUsuario.textContent = data.saldo.toFixed(2);
            });
    }

    // Inicializar
    cargarApuestas();
    actualizarSaldo();
    calcularProbabilidad(equipoSelect.value);
});
