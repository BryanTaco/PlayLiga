from mitorneo.models import Partido
from django.utils import timezone

def listar_proximos_partidos():
    partidos = Partido.objects.filter(fecha__gte=timezone.now()).order_by('fecha')
    for partido in partidos:
        print(f"ID: {partido.id}, {partido.equipo_local.nombre} vs {partido.equipo_visitante.nombre}, Fecha: {partido.fecha}")

if __name__ == "__main__":
    listar_proximos_partidos()
