from mitorneo.models import Equipo, Partido, Arbitro
from django.utils import timezone
from datetime import timedelta

def crear_partidos_prueba():
    # Obtener o crear equipos
    equipo1, _ = Equipo.objects.get_or_create(nombre="Equipo A")
    equipo2, _ = Equipo.objects.get_or_create(nombre="Equipo B")
    equipo3, _ = Equipo.objects.get_or_create(nombre="Equipo C")

    # Obtener o crear arbitro
    arbitro, _ = Arbitro.objects.get_or_create(nombre="Juan", apellido="Perez", correo="juan.perez@example.com", usuario_id=1)

    # Crear partidos con fechas futuras
    ahora = timezone.now()
    Partido.objects.create(equipo_local=equipo1, equipo_visitante=equipo2, arbitro=arbitro, fecha=ahora + timedelta(days=1))
    Partido.objects.create(equipo_local=equipo2, equipo_visitante=equipo3, arbitro=arbitro, fecha=ahora + timedelta(days=2))
    Partido.objects.create(equipo_local=equipo3, equipo_visitante=equipo1, arbitro=arbitro, fecha=ahora + timedelta(days=3))

if __name__ == "__main__":
    crear_partidos_prueba()
    print("Partidos de prueba creados con fechas futuras.")
