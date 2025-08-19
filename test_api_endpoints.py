#!/usr/bin/env python
"""
Script completo de pruebas para todos los endpoints de la API
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, headers=None, expected_status=200):
    """Prueba un endpoint específico"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        
        status_ok = response.status_code == expected_status
        
        print(f"{'✅' if status_ok else '❌'} {method} {endpoint} - Status: {response.status_code}")
        
        if not status_ok:
            print(f"   Expected: {expected_status}, Got: {response.status_code}")
            if response.text:
                print(f"   Response: {response.text[:200]}...")
        
        return status_ok, response
        
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return False, None

def test_all_endpoints():
    """Prueba todos los endpoints de la API"""
    print("🌐 Probando todos los endpoints de la API...\n")
    
    # Endpoints públicos (GET)
    public_endpoints = [
        "/torneo/",
        "/torneo/login/",
        "/torneo/registro/jugador/",
        "/torneo/registro/arbitro/",
        "/torneo/registro/apostador/",
        "/torneo/api/equipos/",
        "/torneo/api/jugadores/",
        "/torneo/api/arbitros/",
        "/torneo/api/partidos/",
        "/torneo/api/estadisticas_equipo/",
        "/torneo/api/bfs_graph/",
    ]
    
    passed = 0
    total = 0
    
    print("📋 Probando endpoints públicos:")
    for endpoint in public_endpoints:
        total += 1
        success, _ = test_endpoint('GET', endpoint)
        if success:
            passed += 1
    
    print(f"\n📊 Resultados: {passed}/{total} endpoints públicos funcionando")
    
    # Probar endpoints que requieren datos específicos
    print("\n🔍 Probando endpoints con IDs específicos:")
    
    # Estos pueden fallar si no hay datos, pero no deberían dar error 500
    detail_endpoints = [
        ("/torneo/api/equipo/1/", 404),  # Puede no existir
        ("/torneo/api/partido/1/", 404),  # Puede no existir
        ("/torneo/resultado/1/", 404),   # Puede no existir
    ]
    
    for endpoint, expected in detail_endpoints:
        total += 1
        success, response = test_endpoint('GET', endpoint, expected_status=expected)
        if success or (response and response.status_code in [200, 404]):
            passed += 1
    
    print(f"\n📊 Resultados finales: {passed}/{total} endpoints funcionando correctamente")
    
    return passed == total

def test_server_running():
    """Verifica que el servidor esté ejecutándose"""
    try:
        response = requests.get(f"{BASE_URL}/torneo/", timeout=5)
        return True
    except requests.exceptions.RequestException:
        return False

def main():
    print("🚀 Iniciando pruebas exhaustivas de endpoints\n")
    
    # Verificar que el servidor esté corriendo
    print("🔍 Verificando que el servidor esté ejecutándose...")
    if not test_server_running():
        print("❌ El servidor no está ejecutándose en localhost:8000")
        print("   Ejecuta: python manage.py runserver")
        return False
    
    print("✅ Servidor detectado en localhost:8000\n")
    
    # Ejecutar todas las pruebas
    success = test_all_endpoints()
    
    if success:
        print("\n🎉 ¡Todas las pruebas de API pasaron exitosamente!")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisar los errores anteriores.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
