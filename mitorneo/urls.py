from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # si usas
    path('login/', views.login_view, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('registro/jugador/', views.registro_jugador, name='registro_jugador'),
    path('registro/arbitro/', views.registro_arbitro, name='registro_arbitro'),
    path("panel_admin/", views.panel_admin, name="panel_admin"),
    path('panel_jugador/', views.panel_jugador, name='panel_jugador'),
    path('panel_arbitro/', views.panel_arbitro, name='panel_arbitro'),
    path('resultado/<int:partido_id>/', views.resultado_partido, name='resultado_partido'),
    path('api/equipos/', views.api_equipos, name='api_equipos'),
    path('api/arbitros/', views.api_arbitros, name='api_arbitros'),
    path('api/jugadores/', views.api_jugadores, name='api_jugadores'),
    path('api/partidos/', views.api_partidos, name='api_partidos'),
    path('api/agregar_equipo/', views.api_agregar_equipo, name='api_agregar_equipo'),
    path('api/crear_partido/', views.api_crear_partido, name='api_crear_partido'),
    path('api/asignar_jugador/', views.api_asignar_jugador, name='api_asignar_jugador'),
]