from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .models import Usuario, Jugador, Arbitro, Equipo, Partido, Apuesta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_datetime, parse_date
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
import json
from collections import deque

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


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Jugador, Equipo
import json
from django.http import JsonResponse, HttpResponseBadRequest

@login_required
@user_passes_test(lambda u: u.is_authenticated and u.rol == 'admin')
def admin_asignar_jugador_page(request):
    jugadores = Jugador.objects.all()
    equipos = Equipo.objects.all()
    return render(request, 'mitorneo/admin_asignar_jugador.html', {
        'jugadores': jugadores,
        'equipos': equipos,
    })


@login_required
def api_bfs_graph(request):
    """
    API endpoint to return BFS traversal of the tournament graph.
    The graph nodes are teams, edges are matches between teams.
    """
    # Build adjacency list for teams based on matches
    equipos = list(Equipo.objects.all())
    partidos = Partido.objects.all()

    graph = {equipo.id: set() for equipo in equipos}
    for partido in partidos:
        graph[partido.equipo_local.id].add(partido.equipo_visitante.id)
        graph[partido.equipo_visitante.id].add(partido.equipo_local.id)

    # BFS traversal starting from a given team (optional query param)
    start_team_id = request.GET.get('start_team_id')
    if start_team_id:
        try:
            start_team_id = int(start_team_id)
        except ValueError:
            return HttpResponseBadRequest("Invalid start_team_id")
    else:
        # Default to first team if not provided
        if equipos:
            start_team_id = equipos[0].id
        else:
            return JsonResponse({'graph': {}, 'order': []})

    visited = set()
    order = []
    queue = deque([start_team_id])
    visited.add(start_team_id)

    while queue:
        current = queue.popleft()
        order.append(current)
        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    # Return BFS order and graph adjacency list
    return JsonResponse({
        'graph': {str(k): list(v) for k, v in graph.items()},
        'order': order,
    })


@login_required
def apuestas_page(request):
    """
    Render the interactive betting page.
    """
    equipos = Equipo.objects.all()
    return render(request, 'mitorneo/apuestas.html', {'equipos': equipos})


@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
def api_apuestas(request):
    """
    API endpoint to get and post bets.
    GET: return all bets of the logged-in user.
    POST: create a new bet.
    """
    if request.method == 'GET':
        apuestas = Apuesta.objects.filter(usuario=request.user)
        data = [{
            'id': apuesta.id,
            'equipo': apuesta.equipo.nombre,
            'monto': float(apuesta.monto),
            'fecha_apuesta': apuesta.fecha_apuesta.isoformat(),
            'ganador': getattr(apuesta, 'ganador', False)
        } for apuesta in apuestas]
        return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            equipo_id = data.get('equipo_id')
            monto = data.get('monto', 0)

            if not equipo_id:
                return HttpResponseBadRequest('Falta equipo_id')

            equipo = get_object_or_404(Equipo, id=equipo_id)

            apuesta = Apuesta.objects.create(
                usuario=request.user,
                equipo=equipo,
                monto=monto
            )
            return JsonResponse({
                'id': apuesta.id,
                'equipo': apuesta.equipo.nombre,
                'monto': float(apuesta.monto),
                'fecha_apuesta': apuesta.fecha_apuesta.isoformat(),
                'ganador': False
            })
        except Exception as e:
            return HttpResponseBadRequest(str(e))


@login_required
@user_passes_test(lambda u: u.is_authenticated and u.rol == 'admin')
def admin_ganadores_apuestas(request):
    """
    Admin page to view bet winners.
    """
    apuestas = Apuesta.objects.all()
    # For demonstration, mark bets on teams that won any match as winners
    # This logic can be improved based on actual match results
    equipos_ganadores = set()
    partidos = Partido.objects.all()
    for partido in partidos:
        # Assuming equipo_local is winner for demo
        equipos_ganadores.add(partido.equipo_local.id)

    for apuesta in apuestas:
        apuesta.ganador = apuesta.equipo.id in equipos_ganadores

    return render(request, 'mitorneo/admin_ganadores_apuestas.html', {'apuestas': apuestas})

@login_required
@user_passes_test(lambda u: u.is_authenticated and u.rol == 'admin')
def permutaciones_combinaciones_page(request):
    """
    Render the permutations and combinations statistics page.
    """
    equipos = Equipo.objects.all()
    return render(request, 'mitorneo/permutaciones_combinaciones.html', {'equipos': equipos})

@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["POST"])
def api_asignar_jugador(request):
    try:
        data = json.loads(request.body)
        jugador_id = data.get('jugador_id')
        equipo_id = data.get('equipo_id')
        posicion = data.get('posicion')

        if not jugador_id or not equipo_id:
            return HttpResponseBadRequest('Faltan datos')

        jugador = get_object_or_404(Jugador, id=jugador_id)
        equipo = get_object_or_404(Equipo, id=equipo_id)

        jugador.equipo = equipo
        if posicion is not None:
            jugador.posicion = posicion
        jugador.save()

        return JsonResponse({'status': 'jugador asignado'})
    except Exception as e:
        return HttpResponseBadRequest(str(e))
