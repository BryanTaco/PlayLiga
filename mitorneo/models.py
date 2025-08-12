from django.db import models
from django.contrib.auth.models import AbstractUser

# Roles de usuario con mejor estructura
USER_ROLES = [
    ('admin', 'Administrador'),
    ('arbitro', 'Árbitro'),
    ('jugador', 'Jugador'),
    ('apostador', 'Apostador'),
]

# Usuario personalizado con rol mejorado
class Usuario(AbstractUser):
    rol = models.CharField(max_length=20, choices=USER_ROLES, default='apostador')
    saldo_real = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def es_admin(self):
        return self.rol == 'admin'

    def es_arbitro(self):
        return self.rol == 'arbitro'

    def es_jugador(self):
        return self.rol == 'jugador'

    def es_apostador(self):
        return self.rol == 'apostador'

    @property
    def saldo(self):
        # Saldo total = saldo_real + ganancias de apuestas - gastos de apuestas
        apuestas = self.apuestas.all()
        ganancias = sum([apuesta.monto for apuesta in apuestas if apuesta.ganador])
        gastos = sum([apuesta.monto for apuesta in apuestas])
        return self.saldo_real + ganancias - gastos


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
    # Removed correo field as requested
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='jugadores')
    posicion = models.CharField(max_length=50, null=True, blank=True)
    numero_camiseta = models.IntegerField(null=True, blank=True)
    biografia = models.TextField(null=True, blank=True)
    partidos_jugados = models.IntegerField(default=0)
    goles = models.IntegerField(default=0)
    asistencias = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Partido(models.Model):
    fecha = models.DateTimeField()  # Ya incluye fecha y hora
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
    ganador = models.BooleanField(default=False)

    def __str__(self):
        return f"Apuesta de {self.usuario.username} en {self.equipo.nombre} por {self.monto}"

    class Meta:
        verbose_name = "Apuesta"
        verbose_name_plural = "Apuestas"


class RecargaSaldo(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='recargas')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=50)
    datos_pago = models.TextField(blank=True, null=True)
    fecha_recarga = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recarga de {self.monto} por {self.usuario.username} via {self.metodo_pago}"


# Modelo de auditoría para roles
class AuditoriaRol(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    rol_anterior = models.CharField(max_length=20, choices=USER_ROLES)
    rol_nuevo = models.CharField(max_length=20, choices=USER_ROLES)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    cambiado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='auditorias_realizadas')

    def __str__(self):
        return f"{self.usuario.username}: {self.rol_anterior} → {self.rol_nuevo} por {self.cambiado_por.username}"
