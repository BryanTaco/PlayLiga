from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Usuario, Equipo, Arbitro, Jugador, Partido, Apuesta, RecargaSaldo, AuditoriaRol

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'rol', 'email', 'saldo_real', 'is_active', 'date_joined')
    list_filter = ('rol', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    fieldsets = (
        ('Información Personal', {
            'fields': ('username', 'first_name', 'last_name', 'email')
        }),
        ('Configuración de Cuenta', {
            'fields': ('rol', 'saldo_real', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Fechas Importantes', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cantidad_jugadores', 'partidos_jugados')
    search_fields = ('nombre',)
    inlines = []
    
    def cantidad_jugadores(self, obj):
        return obj.jugadores.count()
    cantidad_jugadores.short_description = 'Jugadores'
    
    def partidos_jugados(self, obj):
        return obj.partidos_local.count() + obj.partidos_visitante.count()
    partidos_jugados.short_description = 'Partidos'

@admin.register(Arbitro)
class ArbitroAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'correo', 'usuario_link', 'partidos_arbitrados')
    search_fields = ('nombre', 'apellido', 'correo')
    list_filter = ('usuario__is_active',)
    
    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    nombre_completo.short_description = 'Nombre Completo'
    
    def usuario_link(self, obj):
        if obj.usuario:
            url = reverse('admin:mitorneo_usuario_change', args=[obj.usuario.pk])
            return format_html('<a href="{}">{}</a>', url, obj.usuario.username)
        return '-'
    usuario_link.short_description = 'Usuario'
    
    def partidos_arbitrados(self, obj):
        return obj.partidos_arbitrados.count()
    partidos_arbitrados.short_description = 'Partidos'

@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'equipo', 'posicion', 'numero_camiseta', 'estadisticas', 'nivel')
    search_fields = ('nombre', 'apellido', 'correo')
    list_filter = ('equipo', 'posicion', 'nivel')
    readonly_fields = ('usuario_link',)
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'correo', 'usuario_link')
        }),
        ('Información del Equipo', {
            'fields': ('equipo', 'posicion', 'numero_camiseta')
        }),
        ('Estadísticas', {
            'fields': ('nivel', 'partidos_jugados', 'goles', 'asistencias', 'biografia')
        }),
    )
    
    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    nombre_completo.short_description = 'Nombre Completo'
    
    def usuario_link(self, obj):
        if obj.usuario:
            url = reverse('admin:mitorneo_usuario_change', args=[obj.usuario.pk])
            return format_html('<a href="{}">{}</a>', url, obj.usuario.username)
        return '-'
    usuario_link.short_description = 'Usuario'
    
    def estadisticas(self, obj):
        return f"G:{obj.goles} A:{obj.asistencias} PJ:{obj.partidos_jugados}"
    estadisticas.short_description = 'Stats'

@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = ('enfrentamiento', 'fecha', 'arbitro', 'estado_partido', 'resultado_partido')
    list_filter = ('simulado', 'fecha', 'arbitro')
    search_fields = ('equipo_local__nombre', 'equipo_visitante__nombre')
    readonly_fields = ('resultado_display',)
    fieldsets = (
        ('Información del Partido', {
            'fields': ('equipo_local', 'equipo_visitante', 'arbitro', 'fecha')
        }),
        ('Resultado', {
            'fields': ('goles_local', 'goles_visitante', 'simulado', 'ganador', 'resultado_display')
        }),
    )
    
    def enfrentamiento(self, obj):
        return f"{obj.equipo_local} vs {obj.equipo_visitante}"
    enfrentamiento.short_description = 'Partido'
    
    def estado_partido(self, obj):
        if obj.simulado:
            return format_html('<span style="color: green;">✓ Simulado</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pendiente</span>')
    estado_partido.short_description = 'Estado'
    
    def resultado_partido(self, obj):
        if obj.goles_local is not None and obj.goles_visitante is not None:
            return f"{obj.goles_local} - {obj.goles_visitante}"
        return '-'
    resultado_partido.short_description = 'Resultado'
    
    def resultado_display(self, obj):
        if obj.simulado and obj.ganador:
            return format_html(
                '<strong>Ganador:</strong> {} <br><strong>Resultado:</strong> {} - {}',
                obj.ganador.nombre,
                obj.goles_local or 0,
                obj.goles_visitante or 0
            )
        return 'Partido no simulado'
    resultado_display.short_description = 'Detalles del Resultado'

@admin.register(Apuesta)
class ApuestaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'partido_info', 'equipo', 'monto', 'estado_apuesta', 'fecha_apuesta')
    list_filter = ('ganador', 'fecha_apuesta', 'equipo')
    search_fields = ('usuario__username', 'equipo__nombre')
    readonly_fields = ('fecha_apuesta',)
    
    def partido_info(self, obj):
        return f"{obj.partido.equipo_local} vs {obj.partido.equipo_visitante}"
    partido_info.short_description = 'Partido'
    
    def estado_apuesta(self, obj):
        if obj.ganador:
            return format_html('<span style="color: green; font-weight: bold;">✓ Ganadora</span>')
        elif obj.partido.simulado:
            return format_html('<span style="color: red;">✗ Perdedora</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pendiente</span>')
    estado_apuesta.short_description = 'Estado'

@admin.register(RecargaSaldo)
class RecargaSaldoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'monto', 'metodo_pago', 'fecha_recarga')
    list_filter = ('metodo_pago', 'fecha_recarga')
    search_fields = ('usuario__username',)
    readonly_fields = ('fecha_recarga',)

@admin.register(AuditoriaRol)
class AuditoriaRolAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol_anterior', 'rol_nuevo', 'cambiado_por', 'fecha_cambio')
    list_filter = ('rol_anterior', 'rol_nuevo', 'fecha_cambio')
    search_fields = ('usuario__username', 'cambiado_por__username')
    readonly_fields = ('fecha_cambio',)
    
    def has_add_permission(self, request):
        return False  # No permitir agregar manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # No permitir editar

# Personalización del sitio de administración
admin.site.site_header = "PlayLiga - Administración"
admin.site.site_title = "PlayLiga Admin"
admin.site.index_title = "Panel de Administración del Torneo"
