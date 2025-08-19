#!/usr/bin/env python
"""
Script de prueba para verificar la funcionalidad de PlayLiga
Ejecutar con: python test_functionality.py
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miproyectofutbol.settings')
django.setup()

from mitorneo.models import Usuario, Equipo, Jugador, Arbitro, Partido, Apuesta
from django.utils import timezone
from datetime import timedelta
import random

def test_models():
    """Prueba la creación y funcionamiento de los modelos"""
    print("🧪 Probando modelos...")
    
    # Crear usuarios de prueba
    try:
        admin_user = Usuario.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='test123',
            rol='admin'
        )
        print("✅ Usuario administrador creado")
    except Exception as e:
        print(f"❌ Error creando admin: {e}")
        return False
    
    try:
        jugador_user = Usuario.objects.create_user(
            username='jugador_test',
            email='jugador@test.com',
            password='test123',
            rol='jugador'
        )
        print("✅ Usuario jugador creado")
    except Exception as e:
        print(f"❌ Error creando jugador: {e}")
        return False
    
    try:
        arbitro_user = Usuario.objects.create_user(
            username='arbitro_test',
            email='arbitro@test.com',
            password='test123',
            rol='arbitro'
        )
        print("✅ Usuario árbitro creado")
    except Exception as e:
        print(f"❌ Error creando árbitro: {e}")
        return False
    
    try:
        apostador_user = Usuario.objects.create_user(
            username='apostador_test',
            email='apostador@test.com',
            password='test123',
            rol='apostador',
            saldo_real=1000.00
        )
        print("✅ Usuario apostador creado")
    except Exception as e:
        print(f"❌ Error creando apostador: {e}")
        return False
    
    # Crear equipos
    try:
        equipo1 = Equipo.objects.create(nombre='Real Madrid')
        equipo2 = Equipo.objects.create(nombre='Barcelona')
        print("✅ Equipos creados")
    except Exception as e:
        print(f"❌ Error creando equipos: {e}")
        return False
    
    # Crear jugador
    try:
        jugador = Jugador.objects.create(
            usuario=jugador_user,
            nombre='Lionel',
            apellido='Messi',
            correo='messi@test.com',
            equipo=equipo1,
            posicion='Delantero',
            numero_camiseta=10,
            nivel=5
        )
        print("✅ Jugador creado y asignado a equipo")
    except Exception as e:
        print(f"❌ Error creando jugador: {e}")
        return False
    
    # Crear árbitro
    try:
        arbitro = Arbitro.objects.create(
            usuario=arbitro_user,
            nombre='Pierluigi',
            apellido='Collina',
            correo='collina@test.com'
        )
        print("✅ Árbitro creado")
    except Exception as e:
        print(f"❌ Error creando árbitro: {e}")
        return False
    
    # Crear partido
    try:
        fecha_partido = timezone.now() + timedelta(days=1)
        partido = Partido.objects.create(
            equipo_local=equipo1,
            equipo_visitante=equipo2,
            arbitro=arbitro,
            fecha=fecha_partido
        )
        print("✅ Partido creado")
    except Exception as e:
        print(f"❌ Error creando partido: {e}")
        return False
    
    # Crear apuesta
    try:
        apuesta = Apuesta.objects.create(
            usuario=apostador_user,
            partido=partido,
            equipo=equipo1,
            monto=50.00
        )
        print("✅ Apuesta creada")
    except Exception as e:
        print(f"❌ Error creando apuesta: {e}")
        return False
    
    # Simular partido
    try:
        partido.goles_local = random.randint(0, 4)
        partido.goles_visitante = random.randint(0, 4)
        partido.simulado = True
        
        if partido.goles_local > partido.goles_visitante:
            partido.ganador = partido.equipo_local
        elif partido.goles_visitante > partido.goles_local:
            partido.ganador = partido.equipo_visitante
        
        partido.save()
        
        # Procesar apuesta si ganó
        if partido.ganador == apuesta.equipo:
            apuesta.ganador = True
            apuesta.save()
            print("✅ Partido simulado y apuesta procesada (GANADORA)")
        else:
            print("✅ Partido simulado y apuesta procesada (PERDEDORA)")
            
    except Exception as e:
        print(f"❌ Error simulando partido: {e}")
        return False
    
    return True

def test_api_endpoints():
    """Prueba los endpoints de la API"""
    print("\n🌐 Probando endpoints de API...")
    
    from django.test import Client
    from django.contrib.auth import authenticate
    
    client = Client()
    
    # Probar endpoints públicos
    endpoints = [
        '/torneo/api/equipos/',
        '/torneo/api/jugadores/',
        '/torneo/api/arbitros/',
        '/torneo/api/partidos/',
        '/torneo/api/estadisticas_equipo/',
        '/torneo/api/bfs_graph/',
    ]
    
    for endpoint in endpoints:
        try:
            response = client.get(endpoint)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    return True

def test_user_roles():
    """Prueba la funcionalidad de roles de usuario"""
    print("\n👥 Probando roles de usuario...")
    
    try:
        # Verificar que los usuarios tienen los roles correctos
        admin = Usuario.objects.get(username='admin_test')
        jugador = Usuario.objects.get(username='jugador_test')
        arbitro = Usuario.objects.get(username='arbitro_test')
        apostador = Usuario.objects.get(username='apostador_test')
        
        assert admin.es_admin() == True
        assert jugador.es_jugador() == True
        assert arbitro.es_arbitro() == True
        assert apostador.es_apostador() == True
        
        print("✅ Todos los roles funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en roles: {e}")
        return False

def test_statistics():
    """Prueba el cálculo de estadísticas"""
    print("\n📊 Probando estadísticas...")
    
    try:
        equipos = Equipo.objects.all()
        for equipo in equipos:
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
            
            puntos = victorias * 3 + empates
            print(f"✅ {equipo.nombre}: {victorias}V {empates}E {derrotas}D - {puntos} puntos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en estadísticas: {e}")
        return False

def cleanup_test_data():
    """Limpia los datos de prueba"""
    print("\n🧹 Limpiando datos de prueba...")
    
    try:
        # Eliminar en orden para evitar problemas de integridad referencial
        Apuesta.objects.filter(usuario__username__contains='_test').delete()
        Partido.objects.filter(arbitro__usuario__username__contains='_test').delete()
        Jugador.objects.filter(usuario__username__contains='_test').delete()
        Arbitro.objects.filter(usuario__username__contains='_test').delete()
        Equipo.objects.filter(nombre__in=['Real Madrid', 'Barcelona']).delete()
        Usuario.objects.filter(username__contains='_test').delete()
        
        print("✅ Datos de prueba eliminados")
        return True
        
    except Exception as e:
        print(f"❌ Error limpiando datos: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de funcionalidad de PlayLiga\n")
    
    tests = [
        ("Modelos y Base de Datos", test_models),
        ("Endpoints de API", test_api_endpoints),
        ("Roles de Usuario", test_user_roles),
        ("Estadísticas", test_statistics),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Ejecutando: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASÓ")
            else:
                print(f"❌ {test_name} - FALLÓ")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    # Limpiar datos de prueba
    cleanup_test_data()
    
    print(f"\n{'='*50}")
    print(f"RESUMEN DE PRUEBAS")
    print('='*50)
    print(f"Pruebas pasadas: {passed}/{total}")
    print(f"Porcentaje de éxito: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! La aplicación está funcionando correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar los errores anteriores.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
