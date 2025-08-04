from django.contrib import admin
from .models import Usuario, Equipo, Arbitro, Jugador, Partido

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'rol', 'email', 'is_superuser', 'is_staff')
    list_filter = ('rol',)
    search_fields = ('username', 'email')

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Arbitro)
class ArbitroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'correo')
    search_fields = ('nombre', 'apellido', 'correo')

@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'correo', 'nivel', 'equipo')
    search_fields = ('nombre', 'apellido', 'correo')
    list_filter = ('equipo',)

@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'equipo_local', 'equipo_visitante', 'arbitro')
    list_filter = ('arbitro', 'fecha')
    search_fields = ('equipo_local__nombre', 'equipo_visitante__nombre')