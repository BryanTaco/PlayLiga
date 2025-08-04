
from django.db import models
from django.contrib.auth.models import AbstractUser

# Roles de usuario
USER_ROLES = (
    ('admin', 'Administrador'),
    ('arbitro', 'Árbitro'),
    ('jugador', 'Jugador'),
)

# Usuario personalizado
class Usuario(AbstractUser):
    rol = models.CharField(max_length=10, choices=USER_ROLES)

    def es_admin(self):
        return self.rol == 'admin'

    def es_arbitro(self):
        return self.rol == 'arbitro'

    def es_jugador(self):
        return self.rol == 'jugador'


class Equipo(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class Arbitro(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    correo = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Jugador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    nivel = models.IntegerField()
    correo = models.EmailField(unique=True)
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='jugadores')
    posicion = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Partido(models.Model):
    fecha = models.DateTimeField()
    equipo_local = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_local')
    equipo_visitante = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_visitante')
    arbitro = models.ForeignKey(Arbitro, on_delete=models.SET_NULL, null=True, blank=True, related_name='partidos_arbitrados')

    def __str__(self):
        return f"{self.equipo_local} vs {self.equipo_visitante} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"


class Apuesta(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='apuestas')
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='apuestas')
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_apuesta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Apuesta de {self.usuario.username} en {self.equipo.nombre} por {self.monto}"
