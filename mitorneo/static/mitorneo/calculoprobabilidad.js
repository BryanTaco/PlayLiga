function calcularProbabilidades(jugadoresLocal, jugadoresVisitante, equipo1, equipo2) {
    const sumaLocal = jugadoresLocal.reduce((total, jugador) => total + parseInt(jugador.nivel), 0);
    const sumaVisitante = jugadoresVisitante.reduce((total, jugador) => total + parseInt(jugador.nivel), 0);
    const total = sumaLocal + sumaVisitante;

    const probLocal = total === 0 ? 50 : Math.round((sumaLocal / total) * 100);
    const probVisitante = total === 0 ? 50 : 100 - probLocal;

    document.getElementById('equipo1-nombre').textContent = `${equipo1} (${probLocal}%)`;
    document.getElementById('equipo2-nombre').textContent = `${equipo2} (${probVisitante}%)`;

    document.getElementById('equipo1-barra').style.width = probLocal + '%';
    document.getElementById('equipo2-barra').style.width = probVisitante + '%';
}

function generarCombinacionesAlineacion(nombresLocal, nombresVisitante) {
  const posiciones = ["Delantero", "Mediocentro", "Defensa"];
  const contenedor = document.getElementById("combinaciones");

  contenedor.innerHTML = ""; // Limpiar para mostrar nuevas combinaciones

  const crearLista = (jugadores, titulo) => {
    const div = document.createElement("div");
    div.innerHTML = `<h3>${titulo}</h3>`;
    jugadores.forEach(nombre => {
      const posicion = posiciones[Math.floor(Math.random() * posiciones.length)];
      const p = document.createElement("p");
      p.textContent = `${nombre} - Alineación: ${posicion}`;
      div.appendChild(p);
    });
    return div;
  };

  contenedor.appendChild(crearLista(nombresLocal, "Equipo Local"));
  contenedor.appendChild(crearLista(nombresVisitante, "Equipo Visitante"));
}    
