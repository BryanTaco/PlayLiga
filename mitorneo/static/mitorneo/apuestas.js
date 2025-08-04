document.addEventListener('DOMContentLoaded', function () {
    const equipoSelect = document.getElementById('equipo-select');
    const montoInput = document.getElementById('monto-input');
    const apostarBtn = document.getElementById('apostar-btn');
    const apuestasList = document.getElementById('apuestas-list');

    function fetchApuestas() {
        fetch('/torneo/api/apuestas/', {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            apuestasList.innerHTML = '';
            if (data.length === 0) {
                apuestasList.innerHTML = '<li>No tienes apuestas realizadas.</li>';
            } else {
                data.forEach(apuesta => {
                    const li = document.createElement('li');
                    li.textContent = `Equipo: ${apuesta.equipo}, Monto: $${apuesta.monto.toFixed(2)}, Fecha: ${new Date(apuesta.fecha_apuesta).toLocaleString()}`;
                    apuestasList.appendChild(li);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching apuestas:', error);
        });
    }

    apostarBtn.addEventListener('click', function () {
        const equipoId = equipoSelect.value;
        const monto = parseFloat(montoInput.value);

        if (!equipoId) {
            alert('Por favor, selecciona un equipo.');
            return;
        }
        if (isNaN(monto) || monto <= 0) {
            alert('Por favor, ingresa un monto válido mayor que cero.');
            return;
        }

        fetch('/torneo/api/apuestas/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ equipo_id: equipoId, monto: monto }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al realizar la apuesta');
            }
            return response.json();
        })
        .then(data => {
            alert(`Apuesta realizada en ${data.equipo} por $${data.monto.toFixed(2)}`);
            montoInput.value = '';
            equipoSelect.value = '';
            fetchApuestas();
        })
        .catch(error => {
            alert(error.message);
        });
    });

    // Helper function to get CSRF token cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Initial fetch of bets
    fetchApuestas();
});
