from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .models import Usuario, Jugador, Arbitro, Equipo, Partido, Apuesta, RecargaSaldo
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie, get_token
from django.views.decorators.http import require_http_methods, require_GET
from django.utils.dateparse import parse_datetime
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, F, Sum
import json
from collections import deque
import decimal
import math
import random

# Funciones auxiliares para la validación de roles
def es_admin(user):
    return user.is_authenticated and user.rol == 'admin'

def es_jugador(user):
    return user.is_authenticated and user.rol == 'jugador'

def es_arbitro(user):
    return user.is_authenticated and user.rol == 'arbitro'

def es_apostador(user):
    return user.is_authenticated and user.rol == 'apostador'

def home(request):
    return redirect('login')

@ensure_csrf_cookie
def get_csrf_token(request):
    token = get_token(request)
    return JsonResponse({'csrfToken': token})

def login_view(request):
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        rol = request.POST.get('rol')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.rol == rol:
                login(request, user)
                if rol == 'admin':
                    return redirect('panel_admin')
                elif rol == 'jugador':
                    return redirect('panel_jugador')
                elif rol == 'arbitro':
                    return redirect('panel_arbitro')
                elif rol == 'apostador':
                    return redirect('apuestas_page')
            else:
                messages.error(request, 'Rol incorrecto para el usuario.')
        else:
            messages.error(request, 'Usuario o contraseña inválidos.')

    return render(request, 'mitorneo/login.html')

@login_required
def cerrar_sesion(request):
    logout(request)
    return redirect('login')

# mitorneo/views.py

def registro_jugador(request):
    # Define la consulta de equipos fuera del bloque if
    equipos = Equipo.objects.all()
    context = {'equipos': equipos}

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.gfet('apellido', '').strip()
        correo = request.POST.get('correo', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        equipo_id = request.POST.get('equipo')

        # Validaciones
        if not all([nombre, apellido, correo, username, password, equipo_id]):
            messages.error(request, 'Todos los campos son obligatorios.')
            # Al renderizar el error, el contexto con los equipos ya está listo
            return render(request, 'mitorneo/registro_jugador.html', context)

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return render(request, 'mitorneo/registro_jugador.html', context)

        try:
            user = Usuario.objects.create_user(
                username=username,
                email=correo,
                password=password,
                rol='jugador'
            )
            
            equipo_seleccionado = Equipo.objects.get(id=equipo_id)

            Jugador.objects.create(
                usuario=user,
                nombre=nombre,
                apellido=apellido,
                correo=correo,
                nivel=1,
                equipo=equipo_seleccionado
            )
            messages.success(request, 'Registro de jugador exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
        except Equipo.DoesNotExist:
            messages.error(request, 'El equipo seleccionado no es válido.')
        except Exception as e:
            messages.error(request, f'Error al registrar el jugador: {e}')

    # Para peticiones GET, simplemente renderiza la plantilla con el contexto
    return render(request, 'mitorneo/registro_jugador.html', context)

def registro_arbitro(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        correo = request.POST.get('correo', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Validaciones
        if not all([nombre, apellido, correo, username, password]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, 'mitorneo/registro_arbitro.html')

        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return render(request, 'mitorneo/registro_arbitro.html')

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return render(request, 'mitorneo/registro_arbitro.html')

        if Usuario.objects.filter(email=correo).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
            return render(request, 'mitorneo/registro_arbitro.html')
        
        try:
            user = Usuario.objects.create_user(
                username=username,
                email=correo,
                password=password,
                rol='arbitro'
            )
            Arbitro.objects.create(
                usuario=user,
                nombre=nombre,
                apellido=apellido,
                correo=correo
            )
            messages.success(request, 'Registro de árbitro exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error al registrar el árbitro: {e}')
    return render(request, 'mitorneo/registro_arbitro.html')

def registro_apostador(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        correo = request.POST.get('correo', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Validaciones
        if not all([nombre, apellido, correo, username, password]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, 'mitorneo/registro_apostador.html')

        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return render(request, 'mitorneo/registro_apostador.html')

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return render(request, 'mitorneo/registro_apostador.html')

        if Usuario.objects.filter(email=correo).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
            return render(request, 'mitorneo/registro_apostador.html')
        
        try:
            user = Usuario.objects.create_user(
                username=username,
                email=correo,
                password=password,
                rol='apostador',
                first_name=nombre,
                last_name=apellido
            )
            messages.success(request, 'Registro de apostador exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error al registrar el apostador: {e}')
    return render(request, 'mitorneo/registro_apostador.html')

@login_required
@user_passes_test(es_admin)
def panel_admin(request):
    return render(request, 'mitorneo/admin_panel.html')

@login_required
@user_passes_test(es_jugador)
def panel_jugador(request):
    jugador = get_object_or_404(Jugador, usuario=request.user)
    partidos = Partido.objects.filter(
        Q(equipo_local=jugador.equipo) | Q(equipo_visitante=jugador.equipo)
    ).order_by('fecha')
    return render(request, 'mitorneo/jugador_panel.html', {'jugador': jugador, 'partidos': partidos})

@login_required
@user_passes_test(es_arbitro)
def panel_arbitro(request):
    arbitro = get_object_or_404(Arbitro, usuario=request.user)
    partidos = Partido.objects.filter(arbitro=arbitro).order_by('fecha')
    return render(request, 'mitorneo/arbitro_panel.html', {'arbitro': arbitro, 'partidos': partidos})

@login_required
@user_passes_test(es_apostador)
def apuestas_page(request):
    partidos = Partido.objects.filter(simulado=False, fecha__gt=timezone.now()).order_by('fecha')
    return render(request, 'mitorneo/apuestas.html', {'partidos': partidos})

@login_required
def resultado_partido(request, partido_id):
    partido = get_object_or_404(Partido, id=partido_id)
    return render(request, 'mitorneo/resultado.html', {'partido': partido})

# Vistas de API
@require_GET
def api_equipos(request):
    equipos = Equipo.objects.all().values('id', 'nombre')
    return JsonResponse(list(equipos), safe=False)

@require_GET
def api_jugadores(request):
    jugadores = Jugador.objects.all().values('id', 'nombre', 'apellido', 'equipo__nombre', 'equipo_id')
    return JsonResponse(list(jugadores), safe=False)

@require_GET
def api_arbitros(request):
    arbitros = Arbitro.objects.all().values('id', 'nombre', 'apellido')
    return JsonResponse(list(arbitros), safe=False)

@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["POST"])
def api_agregar_equipo(request):
    try:
        data = json.loads(request.body)
        nombre_equipo = data.get('nombre')
        if not nombre_equipo:
            return HttpResponseBadRequest('Nombre de equipo no proporcionado.')
        
        equipo = Equipo.objects.create(nombre=nombre_equipo)
        return JsonResponse({'id': equipo.id, 'nombre': equipo.nombre}, status=201)
    except Exception as e:
        return HttpResponseBadRequest(str(e))

@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["POST"])
def api_crear_partido(request):
    try:
        data = json.loads(request.body)
        equipo_local_id = data.get('equipo_local_id')
        equipo_visitante_id = data.get('equipo_visitante_id')
        arbitro_id = data.get('arbitro_id')
        fecha_str = data.get('fecha')
        
        if not all([equipo_local_id, equipo_visitante_id, arbitro_id, fecha_str]):
            return HttpResponseBadRequest('Faltan datos para crear el partido.')

        equipo_local = get_object_or_404(Equipo, id=equipo_local_id)
        equipo_visitante = get_object_or_404(Equipo, id=equipo_visitante_id)
        arbitro = get_object_or_404(Arbitro, id=arbitro_id)
        fecha = parse_datetime(fecha_str)

        partido = Partido.objects.create(
            equipo_local=equipo_local,
            equipo_visitante=equipo_visitante,
            arbitro=arbitro,
            fecha=fecha
        )
        return JsonResponse({
            'id': partido.id,
            'equipo_local': partido.equipo_local.nombre,
            'equipo_visitante': partido.equipo_visitante.nombre,
            'arbitro': f'{partido.arbitro.nombre} {partido.arbitro.apellido}',
            'fecha': partido.fecha.isoformat()
        }, status=201)
    except Exception as e:
        return HttpResponseBadRequest(str(e))

@require_GET
def api_partidos(request):
    partidos = Partido.objects.all().values(
        'id', 'fecha', 'equipo_local__nombre', 'equipo_visitante__nombre', 
        'arbitro__nombre', 'arbitro__apellido', 'simulado', 'ganador__nombre'
    )
    partidos_list = []
    for p in partidos:
        partidos_list.append({
            'id': p['id'],
            'fecha': p['fecha'],
            'equipo_local': p['equipo_local__nombre'],
            'equipo_visitante': p['equipo_visitante__nombre'],
            'arbitro': f'{p["arbitro__nombre"]} {p["arbitro__apellido"]}',
            'simulado': p['simulado'],
            'ganador': p['ganador__nombre'] if p['ganador__nombre'] else None,
        })
    return JsonResponse(partidos_list, safe=False)

@login_required
@user_passes_test(es_apostador)
@require_http_methods(["GET"])
def api_saldo(request):
    return JsonResponse({'saldo': request.user.saldo})

@csrf_exempt
@login_required
@user_passes_test(es_apostador)
@require_http_methods(["POST"])
def api_recargar_saldo(request):
    try:
        data = json.loads(request.body)
        monto = decimal.Decimal(data.get('monto'))
        metodo = data.get('metodo')
        datos_pago = data.get('datos_pago')

        if monto <= 0:
            return HttpResponseBadRequest('El monto de la recarga debe ser positivo.')
        
        request.user.saldo_real += monto
        request.user.save()
        
        RecargaSaldo.objects.create(
            usuario=request.user,
            monto=monto,
            metodo_pago=metodo,
            datos_pago=datos_pago
        )

        return JsonResponse({'message': 'Recarga realizada con éxito.', 'nuevo_saldo': request.user.saldo}, status=200)

    except (ValueError, decimal.InvalidOperation):
        return HttpResponseBadRequest('Monto inválido.')
    except Exception as e:
        return HttpResponseBadRequest(str(e))

@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["POST"])
def api_simular_partido(request, partido_id):
    try:
        partido = get_object_or_404(Partido, id=partido_id)

        # Simulación de goles
        goles_local = random.randint(0, 5)
        goles_visitante = random.randint(0, 5)

        partido.goles_local = goles_local
        partido.goles_visitante = goles_visitante
        partido.simulado = True
        
        # Determinar ganador
        if goles_local > goles_visitante:
            partido.ganador = partido.equipo_local
        elif goles_visitante > goles_local:
            partido.ganador = partido.equipo_visitante
        # Si es empate, ganador queda como None
        
        partido.save()

        # Procesar apuestas ganadoras
        apuestas_ganadoras = Apuesta.objects.filter(
            partido=partido,
            equipo=partido.ganador
        ) if partido.ganador else []
        
        for apuesta in apuestas_ganadoras:
            apuesta.ganador = True
            apuesta.save()

        return JsonResponse({
            'success': True,
            'goles_local': goles_local,
            'goles_visitante': goles_visitante,
            'ganador': partido.ganador.nombre if partido.ganador else 'Empate',
            'mensaje': 'Partido simulado exitosamente.'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["POST"])
def api_asignar_jugador(request):
    """API para asignar un jugador a un equipo"""
    try:
        data = json.loads(request.body)
        jugador_id = data.get('jugador_id')
        equipo_id = data.get('equipo_id')
        numero_camiseta = data.get('numero_camiseta')
        posicion = data.get('posicion')
        
        if not jugador_id or not equipo_id:
            return JsonResponse({'error': 'Jugador y equipo son requeridos.'}, status=400)
        
        jugador = get_object_or_404(Jugador, id=jugador_id)
        equipo = get_object_or_404(Equipo, id=equipo_id)
        
        # Verificar que el número de camiseta no esté ocupado
        if numero_camiseta:
            if Jugador.objects.filter(equipo=equipo, numero_camiseta=numero_camiseta).exclude(id=jugador_id).exists():
                return JsonResponse({'error': f'El número {numero_camiseta} ya está ocupado en este equipo.'}, status=400)
            jugador.numero_camiseta = numero_camiseta
        
        jugador.equipo = equipo
        if posicion:
            jugador.posicion = posicion
        jugador.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': f'{jugador.nombre} {jugador.apellido} asignado a {equipo.nombre}',
            'jugador': {
                'id': jugador.id,
                'nombre': f'{jugador.nombre} {jugador.apellido}',
                'equipo': equipo.nombre,
                'numero_camiseta': jugador.numero_camiseta,
                'posicion': jugador.posicion
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def api_bfs_graph(request):
    """API para obtener datos del grafo de equipos usando BFS"""
    try:
        # Crear grafo basado en partidos jugados
        equipos = list(Equipo.objects.all())
        partidos = Partido.objects.filter(simulado=True)
        
        # Construir grafo de adyacencia
        grafo = {equipo.id: [] for equipo in equipos}
        for partido in partidos:
            grafo[partido.equipo_local.id].append(partido.equipo_visitante.id)
            grafo[partido.equipo_visitante.id].append(partido.equipo_local.id)
        
        # BFS desde el primer equipo
        if not equipos:
            return JsonResponse({'nodos': [], 'conexiones': []})
        
        visitados = set()
        cola = deque([equipos[0].id])
        visitados.add(equipos[0].id)
        orden_bfs = []
        
        while cola:
            actual = cola.popleft()
            orden_bfs.append(actual)
            
            for vecino in grafo[actual]:
                if vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(vecino)
        
        # Preparar datos para respuesta
        nodos = []
        for equipo in equipos:
            nodos.append({
                'id': equipo.id,
                'nombre': equipo.nombre,
                'visitado': equipo.id in visitados
            })
        
        conexiones = []
        for partido in partidos:
            conexiones.append({
                'origen': partido.equipo_local.id,
                'destino': partido.equipo_visitante.id,
                'partido_id': partido.id
            })
        
        return JsonResponse({
            'nodos': nodos,
            'conexiones': conexiones,
            'orden_bfs': orden_bfs
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def api_equipo_detail(request, equipo_id):
    """API para obtener detalles de un equipo"""
    try:
        equipo = get_object_or_404(Equipo, id=equipo_id)
        jugadores = Jugador.objects.filter(equipo=equipo)
        
        # Estadísticas del equipo
        partidos_local = Partido.objects.filter(equipo_local=equipo, simulado=True)
        partidos_visitante = Partido.objects.filter(equipo_visitante=equipo, simulado=True)
        
        victorias = 0
        empates = 0
        derrotas = 0
        goles_favor = 0
        goles_contra = 0
        
        for partido in partidos_local:
            if partido.goles_local is not None and partido.goles_visitante is not None:
                goles_favor += partido.goles_local
                goles_contra += partido.goles_visitante
                if partido.goles_local > partido.goles_visitante:
                    victorias += 1
                elif partido.goles_local == partido.goles_visitante:
                    empates += 1
                else:
                    derrotas += 1
        
        for partido in partidos_visitante:
            if partido.goles_local is not None and partido.goles_visitante is not None:
                goles_favor += partido.goles_visitante
                goles_contra += partido.goles_local
                if partido.goles_visitante > partido.goles_local:
                    victorias += 1
                elif partido.goles_visitante == partido.goles_local:
                    empates += 1
                else:
                    derrotas += 1
        
        return JsonResponse({
            'equipo': {
                'id': equipo.id,
                'nombre': equipo.nombre,
                'jugadores': [
                    {
                        'id': j.id,
                        'nombre': f'{j.nombre} {j.apellido}',
                        'posicion': j.posicion,
                        'numero_camiseta': j.numero_camiseta,
                        'goles': j.goles,
                        'asistencias': j.asistencias,
                        'partidos_jugados': j.partidos_jugados
                    } for j in jugadores
                ],
                'estadisticas': {
                    'partidos_jugados': victorias + empates + derrotas,
                    'victorias': victorias,
                    'empates': empates,
                    'derrotas': derrotas,
                    'goles_favor': goles_favor,
                    'goles_contra': goles_contra,
                    'diferencia_goles': goles_favor - goles_contra
                }
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def api_partido_detail(request, partido_id):
    """API para obtener detalles de un partido"""
    try:
        partido = get_object_or_404(Partido, id=partido_id)
        
        return JsonResponse({
            'partido': {
                'id': partido.id,
                'fecha': partido.fecha.isoformat(),
                'equipo_local': {
                    'id': partido.equipo_local.id,
                    'nombre': partido.equipo_local.nombre
                },
                'equipo_visitante': {
                    'id': partido.equipo_visitante.id,
                    'nombre': partido.equipo_visitante.nombre
                },
                'arbitro': {
                    'id': partido.arbitro.id if partido.arbitro else None,
                    'nombre': f'{partido.arbitro.nombre} {partido.arbitro.apellido}' if partido.arbitro else None
                },
                'goles_local': partido.goles_local,
                'goles_visitante': partido.goles_visitante,
                'simulado': partido.simulado,
                'ganador': {
                    'id': partido.ganador.id if partido.ganador else None,
                    'nombre': partido.ganador.nombre if partido.ganador else None
                },
                'resultado': partido.resultado if hasattr(partido, 'resultado') else None
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
@user_passes_test(es_apostador)
@require_http_methods(["POST"])
def api_apuestas(request):
    """API para realizar apuestas"""
    try:
        data = json.loads(request.body)
        partido_id = data.get('partido_id')
        equipo_id = data.get('equipo_id')
        monto = decimal.Decimal(str(data.get('monto', 0)))
        
        if not partido_id or not equipo_id or monto <= 0:
            return JsonResponse({'error': 'Datos de apuesta inválidos.'}, status=400)
        
        partido = get_object_or_404(Partido, id=partido_id)
        equipo = get_object_or_404(Equipo, id=equipo_id)
        
        # Verificar que el partido no haya comenzado
        if partido.fecha <= timezone.now():
            return JsonResponse({'error': 'No se puede apostar en partidos que ya comenzaron.'}, status=400)
        
        # Verificar que el equipo participe en el partido
        if equipo not in [partido.equipo_local, partido.equipo_visitante]:
            return JsonResponse({'error': 'El equipo no participa en este partido.'}, status=400)
        
        # Verificar saldo suficiente
        if request.user.saldo < monto:
            return JsonResponse({'error': 'Saldo insuficiente.'}, status=400)
        
        # Crear apuesta
        apuesta = Apuesta.objects.create(
            usuario=request.user,
            partido=partido,
            equipo=equipo,
            monto=monto
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Apuesta realizada exitosamente.',
            'apuesta': {
                'id': apuesta.id,
                'partido': f'{partido.equipo_local.nombre} vs {partido.equipo_visitante.nombre}',
                'equipo_apostado': equipo.nombre,
                'monto': float(monto),
                'fecha': apuesta.fecha_apuesta.isoformat()
            },
            'nuevo_saldo': float(request.user.saldo - monto)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(es_admin)
def admin_asignar_jugador_page(request):
    """Página de administración para asignar jugadores a equipos"""
    return render(request, 'mitorneo/admin_asignar_jugador.html')

@login_required
@user_passes_test(es_admin)
def admin_ganadores_apuestas(request):
    """Página de administración para ver ganadores de apuestas"""
    apuestas_ganadoras = Apuesta.objects.filter(ganador=True).select_related('usuario', 'equipo', 'partido')
    return render(request, 'mitorneo/admin_ganadores_apuestas.html', {
        'apuestas_ganadoras': apuestas_ganadoras
    })

@login_required
def permutaciones_combinaciones_page(request):
    """Página para mostrar permutaciones y combinaciones"""
    return render(request, 'mitorneo/permutaciones_combinaciones.html')

@require_GET
def api_estadisticas_equipo(request):
    """API para obtener estadísticas de todos los equipos"""
    try:
        equipos_stats = []
        
        for equipo in Equipo.objects.all():
            partidos_local = Partido.objects.filter(equipo_local=equipo, simulado=True)
            partidos_visitante = Partido.objects.filter(equipo_visitante=equipo, simulado=True)
            
            victorias = empates = derrotas = 0
            goles_favor = goles_contra = 0
            
            for partido in partidos_local:
                if partido.goles_local is not None and partido.goles_visitante is not None:
                    goles_favor += partido.goles_local
                    goles_contra += partido.goles_visitante
                    if partido.goles_local > partido.goles_visitante:
                        victorias += 1
                    elif partido.goles_local == partido.goles_visitante:
                        empates += 1
                    else:
                        derrotas += 1
            
            for partido in partidos_visitante:
                if partido.goles_local is not None and partido.goles_visitante is not None:
                    goles_favor += partido.goles_visitante
                    goles_contra += partido.goles_local
                    if partido.goles_visitante > partido.goles_local:
                        victorias += 1
                    elif partido.goles_visitante == partido.goles_local:
                        empates += 1
                    else:
                        derrotas += 1
            
            partidos_jugados = victorias + empates + derrotas
            puntos = victorias * 3 + empates
            
            equipos_stats.append({
                'equipo': equipo.nombre,
                'partidos_jugados': partidos_jugados,
                'victorias': victorias,
                'empates': empates,
                'derrotas': derrotas,
                'goles_favor': goles_favor,
                'goles_contra': goles_contra,
                'diferencia_goles': goles_favor - goles_contra,
                'puntos': puntos
            })
        
        # Ordenar por puntos y diferencia de goles
        equipos_stats.sort(key=lambda x: (x['puntos'], x['diferencia_goles']), reverse=True)
        
        return JsonResponse({'estadisticas': equipos_stats})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
