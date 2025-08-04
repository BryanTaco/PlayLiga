from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import Usuario, Jugador, Arbitro, Equipo, Partido
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
import json
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import Equipo, Arbitro, Jugador, Partido
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.dateparse import parse_datetime, parse_date
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

def home(request):
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        rol = request.POST.get('rol')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            
            if rol == 'admin' and user.rol == 'admin':
                return redirect('panel_admin')
            elif rol == 'jugador' and user.rol == 'jugador':
                try:
                    jugador = Jugador.objects.get(usuario=user)
                    return redirect('panel_jugador')
                except Jugador.DoesNotExist:
                    messages.error(request, 'Jugador no encontrado.')
            elif rol == 'arbitro' and user.rol == 'arbitro':
                try:               
                   return redirect('panel_arbitro')
                except Arbitro.DoesNotExist:
                    messages.error(request, 'Árbitro no encontrado.')
            else:
                messages.error(request, 'Rol inválido para este usuario.')

        else:
            messages.error(request, 'Credenciales incorrectas.')

        return render(request, 'mitorneo/login.html')
    
    return render(request, 'mitorneo/login.html')

def registro_jugador(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        apellido = request.POST['apellido']
        nivel = request.POST['nivel']
        correo = request.POST['correo']
        username = request.POST['username']
        password = request.POST['password']

        user = Usuario.objects.create_user(
            username=username,
            email=correo,
            password=password,
            rol='jugador',
            first_name=nombre,
            last_name=apellido
        )
        Jugador.objects.create(
            usuario=user,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            nivel=nivel
        )
        return redirect('login')
    return render(request, 'mitorneo/registro_jugador.html')


def registro_arbitro(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        apellido = request.POST['apellido']
        correo = request.POST['correo']
        username = request.POST['username']
        password = request.POST['password']

        user = Usuario.objects.create_user(
            username=username,
            email=correo,
            password=password,
            rol='arbitro',
            first_name=nombre,
            last_name=apellido
        )
        Arbitro.objects.create(
            usuario=user,
            nombre=nombre,
            apellido=apellido,
            correo=correo
        )
        return redirect('login')
    return render(request, 'mitorneo/registro_arbitro.html')

def es_admin(user):
    return user.is_authenticated and user.rol == 'admin'

def es_arbitro(user):
    return hasattr(user, 'usuario') and user.usuario.rol == 'arbitro'


@login_required
@user_passes_test(es_admin)
def panel_admin(request):
    return render(request, 'mitorneo/admin_panel.html')

@login_required
def panel_jugador(request):
    try:
        jugador = Jugador.objects.get(usuario=request.user)
    except Jugador.DoesNotExist:
        return redirect('login')

    equipo = jugador.equipo

    if equipo:
        partidos = Partido.objects.filter(
            Q(equipo_local=equipo) | Q(equipo_visitante=equipo),
            fecha__gte=timezone.now()
        ).order_by('fecha')
    else:
        partidos = []

    return render(request, 'mitorneo/jugador_panel.html', {
        'jugador': jugador,
        'equipo': equipo,
        'partidos': partidos,
    })

@login_required
def panel_arbitro(request):
    arbitro = Arbitro.objects.filter(usuario=request.user).first()
    if not arbitro:
        return redirect('login')  # O mostrar mensaje de error

    partidos = arbitro.partidos_arbitrados.filter(fecha__gte=timezone.now()).order_by('fecha')
    return render(request, 'mitorneo/arbitro_panel.html', {'arbitro': arbitro, 'partidos': partidos})

def cerrar_sesion(request):
    logout(request)
    return redirect('login')


@login_required
@user_passes_test(es_admin)
def api_equipos(request):
    equipos = Equipo.objects.all()
    data = []
    for eq in equipos:
        jugadores = list(eq.jugadores.values('id', 'nombre', 'apellido'))
        data.append({
            'id': eq.id,
            'nombre': eq.nombre,
            'jugadores': jugadores,
        })
    return JsonResponse(data, safe=False)


@login_required
@user_passes_test(es_admin)
def api_arbitros(request):
    arbitros = Arbitro.objects.all()
    data = list(arbitros.values('id', 'nombre', 'apellido'))
    return JsonResponse(data, safe=False)


@login_required
@user_passes_test(es_admin)
def api_jugadores(request):
    jugadores = Jugador.objects.all()
    data = list(jugadores.values('id', 'nombre', 'apellido'))
    return JsonResponse(data, safe=False)

@login_required
@user_passes_test(es_admin)
def resultado_partido(request, partido_id):
    partido = get_object_or_404(Partido, id=partido_id)

    jugadores_local = Jugador.objects.filter(equipo=partido.equipo_local)
    jugadores_visitante = Jugador.objects.filter(equipo=partido.equipo_visitante)

    # En lugar de solo niveles, pasamos nombre + nivel
    niveles_local = [
        {'nombre': jugador.nombre, 'nivel': jugador.nivel}
        for jugador in jugadores_local
    ]
    niveles_visitante = [
        {'nombre': jugador.nombre, 'nivel': jugador.nivel}
        for jugador in jugadores_visitante
    ]

    context = {
        'partido': partido,
        'niveles_local': json.dumps(niveles_local),
        'niveles_visitante': json.dumps(niveles_visitante),
    }

    return render(request, 'mitorneo/resultado.html', context)


@login_required
@user_passes_test(es_admin)
def api_partidos(request):
    partidos = Partido.objects.all().select_related('equipo_local', 'equipo_visitante', 'arbitro')
    data = [
        {
            'id': p.id,  # <--- ¡ASEGÚRATE DE INCLUIR ESTO!
            'equipo_local': p.equipo_local.nombre,
            'equipo_visitante': p.equipo_visitante.nombre,
            'fecha': p.fecha.strftime('%Y-%m-%d'),
            'arbitro': f"{p.arbitro.nombre} {p.arbitro.apellido}"
        } for p in partidos
    ]
    return JsonResponse(data, safe=False)

@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["POST"])
def api_agregar_equipo(request):
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre')
        if not nombre:
            return HttpResponseBadRequest('Falta nombre')
        equipo = Equipo.objects.create(nombre=nombre)
        return JsonResponse({'id': equipo.id, 'nombre': equipo.nombre})
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["POST"])
def api_crear_partido(request):
    try:
        data = json.loads(request.body)
        local_id = data.get('local')
        visitante_id = data.get('visitante')
        arbitro_id = data.get('arbitro')
        fecha_str = data.get('fecha')

        if not (local_id and visitante_id and arbitro_id and fecha_str):
            return HttpResponseBadRequest('Faltan datos')

        local = get_object_or_404(Equipo, id=local_id)
        visitante = get_object_or_404(Equipo, id=visitante_id)
        arbitro = get_object_or_404(Arbitro, id=arbitro_id)
        fecha = parse_date(fecha_str)

        if local == visitante:
            return HttpResponseBadRequest('El equipo local y visitante no pueden ser el mismo')

        partido = Partido.objects.create(
            equipo_local=local,
            equipo_visitante=visitante,
            arbitro=arbitro,
            fecha=fecha
        )
        return JsonResponse({'id': partido.id})
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["POST"])
def api_asignar_jugador(request):
    try:
        data = json.loads(request.body)
        jugador_id = data.get('jugador_id')
        equipo_id = data.get('equipo_id')

        if not jugador_id or not equipo_id:
            return HttpResponseBadRequest('Faltan datos')

        jugador = get_object_or_404(Jugador, id=jugador_id)
        equipo = get_object_or_404(Equipo, id=equipo_id)

        jugador.equipo = equipo
        jugador.save()

        return JsonResponse({'status': 'jugador asignado'})
    except Exception as e:
        return HttpResponseBadRequest(str(e))