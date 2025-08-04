document.addEventListener('DOMContentLoaded', function () {
    cargarDatos();

    document.getElementById('form-agregar-equipo').addEventListener('submit', async function (e) {
        e.preventDefault();
        const nombre = document.getElementById('nombre-equipo').value;

        const resp = await fetch('/torneo/api/agregar_equipo/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': obtenerCSRF()
            },
            body: JSON.stringify({ nombre })
        });

        if (resp.ok) {
            alert("Equipo agregado");
            document.getElementById('form-agregar-equipo').reset();
            cargarDatos();
        }
    });

    document.getElementById('form-crear-partido').addEventListener('submit', async function (e) {
        e.preventDefault();

        const data = {
            local: document.getElementById('equipo-local').value,
            visitante: document.getElementById('equipo-visitante').value,
            arbitro: document.getElementById('arbitro-partido').value,
            fecha: document.getElementById('fecha-partido').value
        };

        const resp = await fetch('/torneo/api/crear_partido/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': obtenerCSRF()
            },
            body: JSON.stringify(data)
        });

        if (resp.ok) {
            alert("Partido creado");
            document.getElementById('form-crear-partido').reset();
            cargarDatos();
        }
    });

    document.getElementById('form-asignar-jugador').addEventListener('submit', async function (e) {
        e.preventDefault();

        const data = {
            jugador_id: document.getElementById('jugador').value,
            equipo_id: document.getElementById('equipo-asignar').value
        };

        const resp = await fetch('/torneo/api/asignar_jugador/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': obtenerCSRF()
            },
            body: JSON.stringify(data)
        });

        if (resp.ok) {
            alert("Jugador asignado");
            cargarDatos();
        }
    });
});

// Helpers

function obtenerCSRF() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim();
        if (c.startsWith(name + '=')) return c.substring(name.length + 1);
    }
    return '';
}

async function cargarDatos() {
    const [equiposResp, arbitrosResp, jugadoresResp, partidosResp] = await Promise.all([
        fetch('/torneo/api/equipos/'),
        fetch('/torneo/api/arbitros/'),
        fetch('/torneo/api/jugadores/'),
        fetch('/torneo/api/partidos/')
    ]);

    const equipos = await equiposResp.json();
    const arbitros = await arbitrosResp.json();
    const jugadores = await jugadoresResp.json();
    const partidos = await partidosResp.json();

    // Poblar selects con texto personalizado en la opción por defecto
    const selectLocal = document.getElementById('equipo-local');
    const selectVisitante = document.getElementById('equipo-visitante');
    const selectEquipoAsignar = document.getElementById('equipo-asignar');
    const selectJugadores = document.getElementById('jugador');
    const selectArbitros = document.getElementById('arbitro-partido');

    selectLocal.innerHTML = '<option value="">Equipo Local</option>';
    selectVisitante.innerHTML = '<option value="">Equipo Visitante</option>';
    selectEquipoAsignar.innerHTML = '<option value="">Seleccionar Equipo</option>';
    selectJugadores.innerHTML = '<option value="">Seleccionar Jugador</option>';
    selectArbitros.innerHTML = '<option value="">Seleccionar Árbitro</option>';

    equipos.forEach(eq => {
        const option = new Option(eq.nombre, eq.id);
        selectLocal.appendChild(option.cloneNode(true));
        selectVisitante.appendChild(option.cloneNode(true));
        selectEquipoAsignar.appendChild(option.cloneNode(true));
    });

    jugadores.forEach(j => {
        const option = new Option(`${j.nombre} ${j.apellido}`, j.id);
        selectJugadores.appendChild(option);
    });

    arbitros.forEach(a => {
        const option = new Option(`${a.nombre} ${a.apellido}`, a.id);
        selectArbitros.appendChild(option);
    });

    // Mostrar vista de equipos
    const contEquipos = document.getElementById('vista-equipos');
    contEquipos.innerHTML = '';
    equipos.forEach(eq => {
        const div = document.createElement('div');
        div.innerHTML = `<strong>${eq.nombre}</strong><ul>${
            eq.jugadores.map(j => `<li>${j.nombre} ${j.apellido}</li>`).join('')
        }</ul>`;
        contEquipos.appendChild(div);
    });

    // Mostrar vista de partidos
    const contPartidos = document.getElementById('vista-partidos');
    contPartidos.innerHTML = '';
    partidos.forEach(p => {
        const div = document.createElement('div');
        div.classList.add('partido-item');

        div.innerHTML = `
            <div class="partido-info">
                <span>${p.equipo_local} vs ${p.equipo_visitante} - ${p.fecha} (Árbitro: ${p.arbitro})</span>
            </div>
            <button class="btn-simular" onclick="window.location.href='/torneo/resultado/${p.id}/'">Simular Victoria</button>
        `;

        contPartidos.appendChild(div);
    });
}

function cerrarSesion() {
    window.location.href = '/torneo/logout/';
}