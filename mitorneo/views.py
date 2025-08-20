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

def registro_jugador(request):
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
                nivel=int(nivel) if nivel else 1,
                equipo=equipo_seleccionado
            )
            messages.success(request, 'Registro de jugador exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
        except Equipo.DoesNotExist:
            messages.error(request, 'El equipo seleccionado no es válido.')
        except Exception as e:
            messages.error(request, f'Error al registrar el jugador: {e}')

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
    return render(request, 'mitorneo/jugador_panel.html', {'jugador': jugador, 'partidos': partidos, 'equipo': jugador.equipo})

@login_required
@user_passes_test(es_arbitro)
def panel_arbitro(request):
    arbitro = get_object_or_404(Arbitro, usuario=request.user)
    partidos = Partido.objects.filter(arbitro=arbitro).order_by('fecha')
    return render(request, 'mitorneo/arbitro_panel.html', {'arbitro': arbitro, 'partidos': partidos})

@login_required
def apuestas_page(request):
    equipos = Equipo.objects.all()
    proximos_partidos = Partido.objects.filter(simulado=False, fecha__gt=timezone.now()).order_by('fecha')
    saldo = request.user.saldo if hasattr(request.user, 'saldo') else 0
    return render(request, 'mitorneo/apuestas.html', {
        'equipos': equipos,
        'proximos_partidos': proximos_partidos,
        'saldo': saldo
    })

@login_required
def resultado_partido(request, partido_id):
    partido = get_object_or_404(Partido, id=partido_id)
    jugadores_local = Jugador.objects.filter(equipo=partido.equipo_local)
    jugadores_visitante = Jugador.objects.filter(equipo=partido.equipo_visitante)
    
    niveles_local = [{'nombre': f'{j.nombre} {j.apellido}', 'nivel': j.nivel} for j in jugadores_local]
    niveles_visitante = [{'nombre': f'{j.nombre} {j.apellido}', 'nivel': j.nivel} for j in jugadores_visitante]
    
    return render(request, 'mitorneo/resultado.html', {
        'partido': partido,
        'niveles_local': json.dumps(niveles_local),
        'niveles_visitante': json.dumps(niveles_visitante)
    })

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
        'arbitro__nombre', 'arbitro__apellido', 'simulado', 'ganador__nombre',
        'goles_local', 'goles_visitante'
    )
    partidos_list = []
    for p in partidos:
        partidos_list.append({
            'id': p['id'],
            'fecha': p['fecha'],
            'equipo_local': p['equipo_local__nombre'],
            'equipo_visitante': p['equipo_visitante__nombre'],
            'arbitro': f'{p["arbitro__nombre"]} {p["arbitro__apellido"]}' if p["arbitro__nombre"] else 'Sin árbitro',
            'simulado': p['simulado'],
            'goles_local': p['goles_local'],
            'goles_visitante': p['goles_visitante'],
            'ganador': p['ganador__nombre'] if p['ganador__nombre'] else None,
        })
    return JsonResponse(partidos_list, safe=False)

@login_required
@require_http_methods(["GET"])
def api_saldo(request):
    return JsonResponse({'saldo': float(request.user.saldo)})

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_recargar_saldo(request):
    try:
        data = json.loads(request.body)
        monto = decimal.Decimal(str(data.get('monto', 0)))
        metodo_pago = data.get('metodo_pago')
        datos_pago = data.get('datos_pago', {})

        if monto <= 0:
            return HttpResponseBadRequest('El monto de la recarga debe ser positivo.')
        if not metodo_pago:
            return HttpResponseBadRequest('El método de pago es obligatorio.')

        # Actualizamos el saldo real del usuario
        request.user.saldo_real = F('saldo_real') + monto
        request.user.save()
        request.user.refresh_from_db()
        
        RecargaSaldo.objects.create(
            usuario=request.user,
            monto=monto,
            metodo_pago=metodo_pago,
            datos_pago=json.dumps(datos_pago)
        )

        return JsonResponse({
            'message': 'Recarga realizada con éxito.', 
            'saldo': float(request.user.saldo),
            'nuevo_saldo': float(request.user.saldo)
        }, status=200)

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
        else:
            partido.ganador = None
        
        partido.save()

        # Procesar apuestas ganadoras
        Apuesta.objects.filter(partido=partido).update(ganador=False)
        if partido.ganador:
            Apuesta.objects.filter(partido=partido, equipo=partido.ganador).update(ganador=True)

        return JsonResponse({
            'success': True,
            'goles_local': goles_local,
            'goles_visitante': goles_visitante,
            'equipo_local': partido.equipo_local.nombre,
            'equipo_visitante': partido.equipo_visitante.nombre,
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
    try:
        data = json.loads(request.body)
        jugador_id = data.get('jugador_id')
        equipo_id = data.get('equipo_id')
        posicion = data.get('posicion')
        
        if not jugador_id or not equipo_id:
            return JsonResponse({'error': 'Jugador y equipo son requeridos.'}, status=400)
        
        jugador = get_object_or_404(Jugador, id=jugador_id)
        equipo = get_object_or_404(Equipo, id=equipo_id)
        
        jugador.equipo = equipo
        if posicion:
            jugador.posicion = posicion
        jugador.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': f'{jugador.nombre} {jugador.apellido} asignado a {equipo.nombre}'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def api_bfs_graph(request):
    try:
        equipos = list(Equipo.objects.all())
        partidos = Partido.objects.filter(simulado=True)
        
        grafo = {equipo.id: [] for equipo in equipos}
        for partido in partidos:
            grafo[partido.equipo_local.id].append(partido.equipo_visitante.id)
            grafo[partido.equipo_visitante.id].append(partido.equipo_local.id)
        
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

@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["PUT", "DELETE"])
def api_equipo_detail(request, equipo_id):
    try:
        equipo = get_object_or_404(Equipo, id=equipo_id)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            nombre = data.get('nombre')
            if nombre:
                equipo.nombre = nombre
                equipo.save()
            return JsonResponse({'success': True, 'mensaje': 'Equipo actualizado'})
        
        elif request.method == 'DELETE':
            equipo.delete()
            return JsonResponse({'success': True, 'mensaje': 'Equipo eliminado'})
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
@user_passes_test(es_admin)
@require_http_methods(["PUT", "DELETE"])
def api_partido_detail(request, partido_id):
    try:
        partido = get_object_or_404(Partido, id=partido_id)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            fecha_str = data.get('fecha')
            if fecha_str:
                fecha = parse_datetime(fecha_str)
                partido.fecha = fecha
                partido.save()
            return JsonResponse({'success': True, 'mensaje': 'Partido actualizado'})
        
        elif request.method == 'DELETE':
            partido.delete()
            return JsonResponse({'success': True, 'mensaje': 'Partido eliminado'})
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def api_apuestas(request):
    if request.method == 'GET':
        try:
            apuestas = Apuesta.objects.filter(usuario=request.user).order_by('-fecha_apuesta')
            data = [{
                'equipo': apuesta.equipo.nombre,
                'monto': float(apuesta.monto),
                'fecha_apuesta': apuesta.fecha_apuesta.isoformat(),
                'ganador': apuesta.ganador
            } for apuesta in apuestas]
            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            partido_id = data.get('partido_id')
            equipo_id = data.get('equipo_id')
            monto = decimal.Decimal(str(data.get('monto', 0)))
            
            if not partido_id or not equipo_id or monto <= 0:
                return JsonResponse({'error': 'Datos de apuesta inválidos.'}, status=400)
            
            partido = get_object_or_404(Partido, id=partido_id)
            equipo = get_object_or_404(Equipo, id=equipo_id)
            
            if partido.fecha <= timezone.now():
                return JsonResponse({'error': 'No se puede apostar en partidos que ya comenzaron.'}, status=400)
            
            if equipo not in [partido.equipo_local, partido.equipo_visitante]:
                return JsonResponse({'error': 'El equipo no participa en este partido.'}, status=400)
            
            if request.user.saldo < monto:
                return JsonResponse({'error': 'Saldo insuficiente.'}, status=400)
            
            # Descontar del saldo
            request.user.saldo_real = F('saldo_real') - monto
            request.user.save()
            request.user.refresh_from_db()
            
            apuesta = Apuesta.objects.create(
                usuario=request.user,
                partido=partido,
                equipo=equipo,
                monto=monto
            )
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Apuesta realizada exitosamente.',
                'nuevo_saldo': float(request.user.saldo)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido.'}, status=405)

@login_required
@user_passes_test(es_admin)
def admin_asignar_jugador_page(request):
    jugadores = Jugador.objects.all()
    equipos = Equipo.objects.all()
    return render(request, 'mitorneo/admin_asignar_jugador.html', {
        'jugadores': jugadores,
        'equipos': equipos
    })

@login_required
@user_passes_test(es_admin)
def admin_ganadores_apuestas(request):
    apuestas = Apuesta.objects.all()
    return render(request, 'mitorneo/admin_ganadores_apuestas.html', {
        'apuestas': apuestas
    })

@login_required
def permutaciones_combinaciones_page(request):
    equipos = Equipo.objects.all()
    return render(request, 'mitorneo/permutaciones_combinaciones.html', {
        'equipos': equipos
    })

@require_GET
def api_estadisticas_equipo(request):
    try:
        equipo_id = request.GET.get('equipo_id')
        if not equipo_id:
            return JsonResponse({'error': 'ID de equipo no proporcionado'}, status=400)
        
        equipo = get_object_or_404(Equipo, id=equipo_id)
        
        # Calcular estadísticas básicas
        partidos_local = Partido.objects.filter(equipo_local=equipo, simulado=True)
        partidos_visitante = Partido.objects.filter(equipo_visitante=equipo, simulado=True)
        
        victorias = 0
        for partido in partidos_local:
            if partido.goles_local and partido.goles_visitante:
                if partido.goles_local > partido.goles_visitante:
                    victorias += 1
        
        for partido in partidos_visitante:
            if partido.goles_local and partido.goles_visitante:
                if partido.goles_visitante > partido.goles_local:
                    victorias += 1
        
        # Calcular permutaciones y combinaciones
        num_jugadores = Jugador.objects.filter(equipo=equipo).count()
        permutaciones = math.factorial(num_jugadores) if num_jugadores <= 10 else "Muy grande"
        combinaciones = math.comb(num_jugadores, 11) if num_jugadores >= 11 else 0
        
        # Calcular ganancias
        ganancias = Apuesta.objects.filter(equipo=equipo, ganador=True).aggregate(
            total=Sum('monto')
        )['total'] or 0
        
        return JsonResponse({
            'victorias': victorias,
            'permutaciones': permutaciones,
            'combinaciones': combinaciones,
            'ganancias': float(ganancias)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)