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
from django.db.models import Q, F, Sum, Count
import json
from collections import deque
import decimal
import math
import random
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Funciones auxiliares para la validación de roles
def es_admin(user):
    return user.is_authenticated and hasattr(user, 'rol') and user.rol == 'admin'

def es_jugador(user):
    return user.is_authenticated and hasattr(user, 'rol') and user.rol == 'jugador'

def es_arbitro(user):
    return user.is_authenticated and hasattr(user, 'rol') and user.rol == 'arbitro'

def es_apostador(user):
    return user.is_authenticated and hasattr(user, 'rol') and user.rol == 'apostador'

def home(request):
    """Redirecciona al login"""
    return redirect('login')

@ensure_csrf_cookie
def get_csrf_token(request):
    """Obtiene el token CSRF para peticiones AJAX"""
    token = get_token(request)
    return JsonResponse({'csrfToken': token})

def login_view(request):
    """Vista de login con soporte para múltiples roles"""
    next_url = request.GET.get('next', '')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        rol = request.POST.get('rol')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if hasattr(user, 'rol') and user.rol == rol:
                login(request, user)
                
                # Redireccionar según el rol
                if rol == 'admin':
                    return redirect('panel_admin')
                elif rol == 'jugador':
                    return redirect('panel_jugador')
                elif rol == 'arbitro':
                    return redirect('panel_arbitro')
                elif rol == 'apostador':
                    # Si hay una URL next, ir ahí, sino a apuestas
                    return redirect(next_url if next_url else 'apuestas_page')
            else:
                messages.error(request, 'Rol incorrecto para el usuario.')
        else:
            messages.error(request, 'Usuario o contraseña inválidos.')

    return render(request, 'mitorneo/login.html')

@login_required
def cerrar_sesion(request):
    """Cierra la sesión del usuario"""
    logout(request)
    messages.success(request, 'Sesión cerrada exitosamente.')
    return redirect('login')

def registro_jugador(request):
    """Registro de nuevos jugadores"""
    equipos = Equipo.objects.all()
    context = {'equipos': equipos}

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()  # CORREGIDO: Era 'gfet' ahora es 'get'
        correo = request.POST.get('correo', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        equipo_id = request.POST.get('equipo')
        nivel = request.POST.get('nivel', 1)

        # Validaciones
        if not all([nombre, apellido, correo, username, password, equipo_id]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, 'mitorneo/registro_jugador.html', context)

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return render(request, 'mitorneo/registro_jugador.html', context)

        if Usuario.objects.filter(email=correo).exists():
            messages.error(request, 'El correo electrónico ya está registrado.')
            return render(request, 'mitorneo/registro_jugador.html', context)

        try:
            # Crear usuario
            user = Usuario.objects.create_user(
                username=username,
                email=correo,
                password=password,
                rol='jugador'
            )
            
            # Obtener equipo
            equipo_seleccionado = Equipo.objects.get(id=equipo_id)

            # Crear jugador
            Jugador.objects.create(
                usuario=user,
                nombre=nombre,
                apellido=apellido,
                correo=correo,
                nivel=int(nivel) if nivel else 1,
                equipo=equipo_seleccionado
            )
            
            messages.success(request, 'Registro de jugador exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
            
        except Equipo.DoesNotExist:
            messages.error(request, 'El equipo seleccionado no es válido.')
        except Exception as e:
            logger.error(f'Error al registrar jugador: {e}')
            messages.error(request, f'Error al registrar el jugador: {e}')

    return render(request, 'mitorneo/registro_jugador.html', context)

def registro_arbitro(request):
    """Registro de nuevos árbitros"""
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
            logger.error(f'Error al registrar árbitro: {e}')
            messages.error(request, f'Error al registrar el árbitro: {e}')
            
    return render(request, 'mitorneo/registro_arbitro.html')

def registro_apostador(request):
    """Registro de nuevos apostadores"""
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
                last_name=apellido,
                saldo_real=decimal.Decimal('100.00')  # Saldo inicial de regalo
            )
            
            messages.success(request, 'Registro exitoso. Te hemos regalado $100 de saldo inicial. ¡Buena suerte!')
            return redirect('login')
            
        except Exception as e:
            logger.error(f'Error al registrar apostador: {e}')
            messages.error(request, f'Error al registrar el apostador: {e}')
            
    return render(request, 'mitorneo/registro_apostador.html')

@login_required
@user_passes_test(es_admin)
def panel_admin(request):
    """Panel de administración"""
    context = {
        'total_equipos': Equipo.objects.count(),
        'total_partidos': Partido.objects.count(),
        'total_jugadores': Jugador.objects.count(),
        'total_arbitros': Arbitro.objects.count(),
    }
    return render(request, 'mitorneo/admin_panel.html', context)

@login_required
@user_passes_test(es_jugador)
def panel_jugador(request):
    """Panel del jugador"""
    try:
        jugador = get_object_or_404(Jugador, id=jugador_id)
        equipo = get_object_or_404(Equipo, id=equipo_id)
        
        # Asignar al equipo
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
                'posicion': jugador.posicion
            }
        })
        
    except Exception as e:
        logger.error(f'Error al asignar jugador: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def api_estadisticas_equipo(request):
    """API para obtener estadísticas de un equipo específico"""
    try:
        equipo_id = request.GET.get('equipo_id')
        
        if not equipo_id:
            # Si no se especifica equipo, devolver estadísticas de todos
            return api_tabla_posiciones(request)
        
        equipo = get_object_or_404(Equipo, id=equipo_id)
        
        # Calcular estadísticas
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
        
        # Calcular permutaciones y combinaciones
        num_jugadores = Jugador.objects.filter(equipo=equipo).count()
        permutaciones = math.factorial(num_jugadores) if num_jugadores <= 10 else "Muy grande"
        combinaciones = math.comb(num_jugadores, 11) if num_jugadores >= 11 else 0
        
        # Calcular ganancias de apuestas
        ganancias = Apuesta.objects.filter(
            equipo=equipo,
            ganador=True
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        return JsonResponse({
            'equipo': equipo.nombre,
            'partidos_jugados': partidos_jugados,
            'victorias': victorias,
            'empates': empates,
            'derrotas': derrotas,
            'goles_favor': goles_favor,
            'goles_contra': goles_contra,
            'diferencia_goles': goles_favor - goles_contra,
            'puntos': puntos,
            'permutaciones': permutaciones,
            'combinaciones': combinaciones,
            'ganancias': float(ganancias)
        })
        
    except Exception as e:
        logger.error(f'Error al obtener estadísticas: {e}')
        return JsonResponse({'error': str(e)}, status=500)

def api_tabla_posiciones(request):
    """API para obtener tabla de posiciones de todos los equipos"""
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
        logger.error(f'Error al obtener tabla de posiciones: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def api_equipo_detail(request, equipo_id):
    """API para obtener detalles completos de un equipo"""
    try:
        equipo = get_object_or_404(Equipo, id=equipo_id)
        jugadores = Jugador.objects.filter(equipo=equipo).order_by('numero_camiseta', 'nombre')
        
        # Estadísticas del equipo
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
        
        return JsonResponse({
            'success': True,
            'equipo': {
                'id': equipo.id,
                'nombre': equipo.nombre,
                'jugadores': [
                    {
                        'id': j.id,
                        'nombre': f'{j.nombre} {j.apellido}',
                        'posicion': j.posicion or 'Sin definir',
                        'numero_camiseta': j.numero_camiseta,
                        'nivel': j.nivel,
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
                    'diferencia_goles': goles_favor - goles_contra,
                    'puntos': victorias * 3 + empates
                }
            }
        })
        
    except Exception as e:
        logger.error(f'Error al obtener detalles del equipo: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def api_partido_detail(request, partido_id):
    """API para obtener detalles de un partido"""
    try:
        partido = get_object_or_404(Partido, id=partido_id)
        
        return JsonResponse({
            'success': True,
            'partido': {
                'id': partido.id,
                'fecha': partido.fecha.isoformat() if partido.fecha else None,
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
                    'nombre': f'{partido.arbitro.nombre} {partido.arbitro.apellido}' if partido.arbitro else 'Sin árbitro'
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
        logger.error(f'Error al obtener detalles del partido: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["PUT", "DELETE"])
def api_equipo_detail(request, equipo_id):
    """API para actualizar o eliminar un equipo"""
    try:
        equipo = get_object_or_404(Equipo, id=equipo_id)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            nombre = data.get('nombre', '').strip()
            
            if not nombre:
                return JsonResponse({'error': 'El nombre es requerido.'}, status=400)
            
            # Verificar duplicados
            if Equipo.objects.filter(nombre__iexact=nombre).exclude(id=equipo_id).exists():
                return JsonResponse({'error': 'Ya existe otro equipo con ese nombre.'}, status=400)
            
            equipo.nombre = nombre
            equipo.save()
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Equipo actualizado exitosamente.',
                'equipo': {
                    'id': equipo.id,
                    'nombre': equipo.nombre
                }
            })
        
        elif request.method == 'DELETE':
            # Verificar si tiene partidos asociados
            partidos_count = Partido.objects.filter(
                Q(equipo_local=equipo) | Q(equipo_visitante=equipo)
            ).count()
            
            if partidos_count > 0:
                return JsonResponse({
                    'error': f'No se puede eliminar el equipo porque tiene {partidos_count} partidos asociados.'
                }, status=400)
            
            nombre_equipo = equipo.nombre
            equipo.delete()
            
            return JsonResponse({
                'success': True,
                'mensaje': f'Equipo {nombre_equipo} eliminado exitosamente.'
            })
            
    except Exception as e:
        logger.error(f'Error al procesar equipo: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["PUT", "DELETE"])
def api_partido_detail(request, partido_id):
    """API para actualizar o eliminar un partido"""
    try:
        partido = get_object_or_404(Partido, id=partido_id)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            fecha_str = data.get('fecha')
            
            if not fecha_str:
                return JsonResponse({'error': 'La fecha es requerida.'}, status=400)
            
            fecha = parse_datetime(fecha_str)
            if not fecha:
                return JsonResponse({'error': 'Formato de fecha inválido.'}, status=400)
            
            partido.fecha = fecha
            partido.save()
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Partido actualizado exitosamente.',
                'partido': {
                    'id': partido.id,
                    'fecha': partido.fecha.isoformat()
                }
            })
        
        elif request.method == 'DELETE':
            # Verificar si tiene apuestas asociadas
            apuestas_count = Apuesta.objects.filter(partido=partido).count()
            
            if apuestas_count > 0:
                return JsonResponse({
                    'error': f'No se puede eliminar el partido porque tiene {apuestas_count} apuestas asociadas.'
                }, status=400)
            
            partido.delete()
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Partido eliminado exitosamente.'
            })
            
    except Exception as e:
        logger.error(f'Error al procesar partido: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def api_bfs_graph(request):
    """API para obtener datos del grafo de equipos usando BFS"""
    try:
        # Crear grafo basado en partidos jugados
        equipos = list(Equipo.objects.all())
        partidos = Partido.objects.filter(simulado=True)
        
        # Construir grafo de adyacencia
        grafo = {equipo.id: set() for equipo in equipos}
        for partido in partidos:
            grafo[partido.equipo_local.id].add(partido.equipo_visitante.id)
            grafo[partido.equipo_visitante.id].add(partido.equipo_local.id)
        
        # BFS desde el primer equipo
        if not equipos:
            return JsonResponse({'nodos': [], 'conexiones': [], 'orden_bfs': []})
        
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
                'visitado': equipo.id in visitados,
                'jugadores': Jugador.objects.filter(equipo=equipo).count()
            })
        
        conexiones = []
        partidos_procesados = set()
        for partido in partidos:
            # Evitar duplicados
            key = tuple(sorted([partido.equipo_local.id, partido.equipo_visitante.id]))
            if key not in partidos_procesados:
                partidos_procesados.add(key)
                conexiones.append({
                    'origen': partido.equipo_local.id,
                    'destino': partido.equipo_visitante.id,
                    'partido_id': partido.id,
                    'resultado': f"{partido.goles_local}-{partido.goles_visitante}" if partido.simulado else "Pendiente"
                })
        
        return JsonResponse({
            'nodos': nodos,
            'conexiones': conexiones,
            'orden_bfs': orden_bfs,
            'total_equipos': len(equipos),
            'total_conexiones': len(conexiones)
        })
        
    except Exception as e:
        logger.error(f'Error al generar grafo BFS: {e}')
        return JsonResponse({'error': str(e)}, status=500)

# Esta es la parte final corregida del views.py
# Reemplaza desde la línea 700 aproximadamente hasta el final del archivo

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
        posicion = data.get('posicion', '')
        
        if not jugador_id or not equipo_id:
            return JsonResponse({'error': 'Jugador y equipo son requeridos.'}, status=400)
        
        jugador = get_object_or_404(Jugador, id=jugador_id)
        equipo = get_object_or_404(Equipo, id=equipo_id)
        
        # Asignar al equipo
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
                'posicion': jugador.posicion
            }
        })
        
    except Exception as e:
        logger.error(f'Error al asignar jugador: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def api_estadisticas_equipo(request):
    """API para obtener estadísticas de un equipo específico"""
    try:
        equipo_id = request.GET.get('equipo_id')
        
        if not equipo_id:
            # Si no se especifica equipo, devolver estadísticas de todos
            return api_tabla_posiciones(request)
        
        equipo = get_object_or_404(Equipo, id=equipo_id)
        
        # Calcular estadísticas
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
        
        # Calcular permutaciones y combinaciones
        num_jugadores = Jugador.objects.filter(equipo=equipo).count()
        permutaciones = math.factorial(num_jugadores) if num_jugadores <= 10 else "Muy grande"
        combinaciones = math.comb(num_jugadores, 11) if num_jugadores >= 11 else 0
        
        # Calcular ganancias de apuestas
        ganancias = Apuesta.objects.filter(
            equipo=equipo,
            ganador=True
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        return JsonResponse({
            'equipo': equipo.nombre,
            'partidos_jugados': partidos_jugados,
            'victorias': victorias,
            'empates': empates,
            'derrotas': derrotas,
            'goles_favor': goles_favor,
            'goles_contra': goles_contra,
            'diferencia_goles': goles_favor - goles_contra,
            'puntos': puntos,
            'permutaciones': permutaciones,
            'combinaciones': combinaciones,
            'ganancias': float(ganancias)
        })
        
    except Exception as e:
        logger.error(f'Error al obtener estadísticas: {e}')
        return JsonResponse({'error': str(e)}, status=500)

def api_tabla_posiciones(request):
    """API para obtener tabla de posiciones de todos los equipos"""
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
        logger.error(f'Error al obtener tabla de posiciones: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def api_equipo_detail(request, equipo_id):
    """API para obtener detalles completos de un equipo"""
    try:
        equipo = get_object_or_404(Equipo, id=equipo_id)
        jugadores = Jugador.objects.filter(equipo=equipo).order_by('numero_camiseta', 'nombre')
        
        # Estadísticas del equipo
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
        
        return JsonResponse({
            'success': True,
            'equipo': {
                'id': equipo.id,
                'nombre': equipo.nombre,
                'jugadores': [
                    {
                        'id': j.id,
                        'nombre': f'{j.nombre} {j.apellido}',
                        'posicion': j.posicion or 'Sin definir',
                        'numero_camiseta': j.numero_camiseta,
                        'nivel': j.nivel,
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
                    'diferencia_goles': goles_favor - goles_contra,
                    'puntos': victorias * 3 + empates
                }
            }
        })
        
    except Exception as e:
        logger.error(f'Error al obtener detalles del equipo: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def api_partido_detail(request, partido_id):
    """API para obtener detalles de un partido"""
    try:
        partido = get_object_or_404(Partido, id=partido_id)
        
        return JsonResponse({
            'success': True,
            'partido': {
                'id': partido.id,
                'fecha': partido.fecha.isoformat() if partido.fecha else None,
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
                    'nombre': f'{partido.arbitro.nombre} {partido.arbitro.apellido}' if partido.arbitro else 'Sin árbitro'
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
        logger.error(f'Error al obtener detalles del partido: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["PUT", "DELETE"])
def api_equipo_detail(request, equipo_id):
    """API para actualizar o eliminar un equipo"""
    try:
        equipo = get_object_or_404(Equipo, id=equipo_id)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            nombre = data.get('nombre', '').strip()
            
            if not nombre:
                return JsonResponse({'error': 'El nombre es requerido.'}, status=400)
            
            # Verificar duplicados
            if Equipo.objects.filter(nombre__iexact=nombre).exclude(id=equipo_id).exists():
                return JsonResponse({'error': 'Ya existe otro equipo con ese nombre.'}, status=400)
            
            equipo.nombre = nombre
            equipo.save()
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Equipo actualizado exitosamente.',
                'equipo': {
                    'id': equipo.id,
                    'nombre': equipo.nombre
                }
            })
        
        elif request.method == 'DELETE':
            # Verificar si tiene partidos asociados
            partidos_count = Partido.objects.filter(
                Q(equipo_local=equipo) | Q(equipo_visitante=equipo)
            ).count()
            
            if partidos_count > 0:
                return JsonResponse({
                    'error': f'No se puede eliminar el equipo porque tiene {partidos_count} partidos asociados.'
                }, status=400)
            
            nombre_equipo = equipo.nombre
            equipo.delete()
            
            return JsonResponse({
                'success': True,
                'mensaje': f'Equipo {nombre_equipo} eliminado exitosamente.'
            })
            
    except Exception as e:
        logger.error(f'Error al procesar equipo: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["PUT", "DELETE"])
def api_partido_detail(request, partido_id):
    """API para actualizar o eliminar un partido"""
    try:
        partido = get_object_or_404(Partido, id=partido_id)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            fecha_str = data.get('fecha')
            
            if not fecha_str:
                return JsonResponse({'error': 'La fecha es requerida.'}, status=400)
            
            fecha = parse_datetime(fecha_str)
            if not fecha:
                return JsonResponse({'error': 'Formato de fecha inválido.'}, status=400)
            
            partido.fecha = fecha
            partido.save()
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Partido actualizado exitosamente.',
                'partido': {
                    'id': partido.id,
                    'fecha': partido.fecha.isoformat()
                }
            })
        
        elif request.method == 'DELETE':
            # Verificar si tiene apuestas asociadas
            apuestas_count = Apuesta.objects.filter(partido=partido).count()
            
            if apuestas_count > 0:
                return JsonResponse({
                    'error': f'No se puede eliminar el partido porque tiene {apuestas_count} apuestas asociadas.'
                }, status=400)
            
            partido.delete()
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Partido eliminado exitosamente.'
            })
            
    except Exception as e:
        logger.error(f'Error al procesar partido: {e}')
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def api_bfs_graph(request):
    """API para obtener datos del grafo de equipos usando BFS"""
    try:
        # Crear grafo basado en partidos jugados
        equipos = list(Equipo.objects.all())
        partidos = Partido.objects.filter(simulado=True)
        
        # Construir grafo de adyacencia
        grafo = {equipo.id: set() for equipo in equipos}
        for partido in partidos:
            grafo[partido.equipo_local.id].add(partido.equipo_visitante.id)
            grafo[partido.equipo_visitante.id].add(partido.equipo_local.id)
        
        # BFS desde el primer equipo
        if not equipos:
            return JsonResponse({'nodos': [], 'conexiones': [], 'orden_bfs': []})
        
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
                'visitado': equipo.id in visitados,
                'jugadores': Jugador.objects.filter(equipo=equipo).count()
            })
        
        conexiones = []
        partidos_procesados = set()
        for partido in partidos:
            # Evitar duplicados
            key = tuple(sorted([partido.equipo_local.id, partido.equipo_visitante.id]))
            if key not in partidos_procesados:
                partidos_procesados.add(key)
                conexiones.append({
                    'origen': partido.equipo_local.id,
                    'destino': partido.equipo_visitante.id,
                    'partido_id': partido.id,
                    'resultado': f"{partido.goles_local}-{partido.goles_visitante}" if partido.simulado else "Pendiente"
                })
        
        return JsonResponse({
            'nodos': nodos,
            'conexiones': conexiones,
            'orden_bfs': orden_bfs,
            'total_equipos': len(equipos),
            'total_conexiones': len(conexiones)
        })
        
    except Exception as e:
        logger.error(f'Error al generar grafo BFS: {e}')
        return JsonResponse({'error': str(e)}, status=500)

# Vistas administrativas adicionales
@login_required
@user_passes_test(es_admin)
def admin_asignar_jugador_page(request):
    """Página de administración para asignar jugadores a equipos"""
    jugadores = Jugador.objects.select_related('equipo').all()
    equipos = Equipo.objects.all()
    
    context = {
        'jugadores': jugadores,
        'equipos': equipos
    }
    return render(request, 'mitorneo/admin_asignar_jugador.html', context)

@login_required
@user_passes_test(es_admin)
def admin_ganadores_apuestas(request):
    """Página de administración para ver ganadores de apuestas"""
    apuestas = Apuesta.objects.select_related(
        'usuario', 'equipo', 'partido__equipo_local', 'partido__equipo_visitante'
    ).order_by('-fecha_apuesta')
    
    # Filtrar por estado si se especifica
    estado = request.GET.get('estado')
    if estado == 'ganadas':
        apuestas = apuestas.filter(ganador=True)
    elif estado == 'perdidas':
        apuestas = apuestas.filter(ganador=False, partido__simulado=True)
    elif estado == 'pendientes':
        apuestas = apuestas.filter(partido__simulado=False)
    
    context = {
        'apuestas': apuestas,
        'total_apostado': apuestas.aggregate(total=Sum('monto'))['total'] or 0,
        'total_ganado': apuestas.filter(ganador=True).aggregate(total=Sum('monto'))['total'] or 0
    }
    return render(request, 'mitorneo/admin_ganadores_apuestas.html', context)

@login_required
def permutaciones_combinaciones_page(request):
    """Página para mostrar permutaciones y combinaciones"""
    equipos = Equipo.objects.annotate(
        num_jugadores=Count('jugadores')
    ).order_by('nombre')
    
    context = {
        'equipos': equipos
    }
    return render(request, 'mitorneo/permutaciones_combinaciones.html', context)