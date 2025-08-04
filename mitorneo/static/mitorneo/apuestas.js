
document.addEventListener("DOMContentLoaded", function () {
    const recargarSaldoBtn = document.getElementById("recargar-saldo-btn");
    if (recargarSaldoBtn) {
        recargarSaldoBtn.addEventListener("click", function(event) {
            event.preventDefault();
            alert("Botón de recarga clickeado"); // Para verificar si se ejecuta el evento
            const modal = document.getElementById("modal-recarga");
            if (modal) {
                modal.style.display = "block";
            }
        });
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
            const datos_pago = ""; // Aquí se pueden agregar más datos si se amplía el formulario

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
                body: JSON.stringify({ monto: monto, metodo_pago: metodo_pago, datos_pago: datos_pago })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error("Error al recargar saldo.");
                }
                return response.json();
            })
            .then(data => {
                alert("Saldo recargado correctamente.");
                actualizarSaldo();
                const modal = document.getElementById("modal-recarga");
                if (modal) {
                    modal.style.display = "none";
                }
                if (montoInput) {
                    montoInput.value = "";
                }
            })
            .catch(error => {
                alert(error.message);
            });
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
        fetch("/api/apuestas/")
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
        fetch(`/api/estadisticas_equipo/?equipo_id=${equipoId}`)
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

        fetch("/api/apuestas/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({
                equipo_id: equipoId,
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
        fetch("/api/saldo/")
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
