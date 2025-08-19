# PlayLiga ⚽

Una aplicación web completa para la gestión de torneos de fútbol con sistema de apuestas integrado, desarrollada con Django.

## 🌟 Características Principales

- **Gestión Completa de Torneos**: Equipos, jugadores, árbitros y partidos
- **Sistema de Apuestas**: Apuestas en tiempo real con procesamiento automático
- **Múltiples Roles de Usuario**: Admin, Jugador, Árbitro, Apostador
- **Simulación de Partidos**: Resultados aleatorios con estadísticas
- **Panel de Administración**: Interfaz web moderna y responsive
- **Estadísticas Avanzadas**: Tablas de posiciones y análisis de rendimiento
- **API RESTful**: Endpoints completos para todas las funcionalidades
- **Análisis de Grafos**: Algoritmo BFS para análisis de conectividad entre equipos

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.8+
- Django 4.0+
- SQLite (incluido con Python)

### Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd PlayLiga
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install django
   ```

4. **Configurar base de datos**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

6. **Iniciar servidor**
   ```bash
   python manage.py runserver
   ```

7. **Acceder a la aplicación**
   - Aplicación: http://localhost:8000/torneo/
   - Admin Django: http://localhost:8000/admin/

## 👥 Roles de Usuario

### 🔧 Administrador
- Gestión completa de equipos y jugadores
- Creación y simulación de partidos
- Asignación de jugadores a equipos
- Visualización de estadísticas globales
- Gestión de apuestas y ganadores

### ⚽ Jugador
- Visualización de partidos de su equipo
- Estadísticas personales
- Información del equipo y compañeros

### 👨‍⚖️ Árbitro
- Visualización de partidos asignados
- Gestión de partidos a arbitrar
- Historial de partidos dirigidos

### 🎲 Apostador
- Sistema completo de apuestas
- Recarga de saldo
- Visualización de apuestas activas
- Historial de ganancias y pérdidas

## 🛠️ Funcionalidades Técnicas

### Modelos de Datos

- **Usuario**: Sistema de autenticación con roles
- **Equipo**: Gestión de equipos de fútbol
- **Jugador**: Información detallada de jugadores
- **Árbitro**: Gestión de árbitros
- **Partido**: Partidos con simulación y resultados
- **Apuesta**: Sistema de apuestas con procesamiento automático
- **RecargaSaldo**: Historial de recargas de saldo
- **AuditoriaRol**: Auditoría de cambios de roles

### APIs Disponibles

#### Endpoints Públicos
- `GET /torneo/api/equipos/` - Lista de equipos
- `GET /torneo/api/jugadores/` - Lista de jugadores
- `GET /torneo/api/arbitros/` - Lista de árbitros
- `GET /torneo/api/partidos/` - Lista de partidos
- `GET /torneo/api/estadisticas_equipo/` - Estadísticas de equipos
- `GET /torneo/api/bfs_graph/` - Análisis de grafo BFS

#### Endpoints de Administración
- `POST /torneo/api/agregar_equipo/` - Crear equipo
- `POST /torneo/api/crear_partido/` - Crear partido
- `POST /torneo/api/asignar_jugador/` - Asignar jugador a equipo
- `POST /torneo/api/partido/{id}/simular/` - Simular partido

#### Endpoints de Detalles
- `GET /torneo/api/equipo/{id}/` - Detalles de equipo
- `GET /torneo/api/partido/{id}/` - Detalles de partido

#### Endpoints de Apuestas
- `POST /torneo/api/apuestas/` - Realizar apuesta
- `GET /torneo/api/saldo/` - Consultar saldo
- `POST /torneo/api/recargar_saldo/` - Recargar saldo

## 🎮 Uso de la Aplicación

### Para Administradores

1. **Crear Equipos**
   - Acceder al panel de administración
   - Usar el formulario "Agregar Equipo"

2. **Registrar Jugadores**
   - Los jugadores se registran desde la página de registro
   - Asignar jugadores a equipos desde el panel admin

3. **Programar Partidos**
   - Seleccionar equipos local y visitante
   - Asignar árbitro y fecha/hora

4. **Simular Partidos**
   - Hacer clic en "Simular" en la lista de partidos
   - El sistema genera resultados automáticamente

### Para Apostadores

1. **Registrarse como Apostador**
   - Usar el formulario de registro de apostador
   - Recargar saldo inicial

2. **Realizar Apuestas**
   - Navegar a la página de apuestas
   - Seleccionar partido y equipo
   - Ingresar monto de apuesta

3. **Ver Resultados**
   - Las apuestas se procesan automáticamente
   - Ver historial en el perfil

## 🔒 Seguridad

- **Autenticación**: Sistema de login con roles
- **Autorización**: Decoradores de permisos por función
- **Validación**: Validación robusta de datos de entrada
- **CSRF Protection**: Protección contra ataques CSRF
- **Sanitización**: Limpieza de datos de entrada

## 📊 Estadísticas y Análisis

### Estadísticas de Equipos
- Partidos jugados, ganados, empatados, perdidos
- Goles a favor y en contra
- Diferencia de goles
- Puntos (3 por victoria, 1 por empate)
- Tabla de posiciones automática

### Análisis de Grafos
- Construcción de grafo basado en partidos jugados
- Algoritmo BFS para análisis de conectividad
- Visualización de relaciones entre equipos

## 🧪 Pruebas

Ejecutar el script de pruebas incluido:

```bash
python test_functionality.py
```

Este script verifica:
- Creación y funcionamiento de modelos
- Endpoints de API
- Roles de usuario
- Cálculo de estadísticas
- Integridad de datos

## 📁 Estructura del Proyecto

```
PlayLiga/
├── manage.py
├── miproyectofutbol/          # Configuración del proyecto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── mitorneo/                  # Aplicación principal
│   ├── models.py              # Modelos de datos
│   ├── views.py               # Vistas y APIs
│   ├── urls.py                # URLs de la aplicación
│   ├── admin.py               # Configuración del admin
│   ├── static/                # Archivos estáticos
│   │   └── mitorneo/
│   │       ├── adminpanel.js  # JavaScript del panel admin
│   │       ├── adminpanel.css # Estilos del panel admin
│   │       └── imagenes/      # Imágenes
│   └── templates/             # Plantillas HTML
│       └── mitorneo/
├── test_functionality.py      # Script de pruebas
├── MEJORAS_REALIZADAS.md      # Documentación de mejoras
└── README.md                  # Este archivo
```

## 🔧 Configuración Avanzada

### Variables de Entorno

Crear archivo `.env` para configuraciones sensibles:

```env
SECRET_KEY=tu_clave_secreta_aqui
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

### Configuración de Producción

Para despliegue en producción:

1. Configurar `DEBUG = False`
2. Configurar `ALLOWED_HOSTS`
3. Usar base de datos PostgreSQL
4. Configurar archivos estáticos con WhiteNoise
5. Usar variables de entorno para configuraciones sensibles

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para nueva funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Commit los cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Para reportar bugs o solicitar nuevas funcionalidades, crear un issue en el repositorio.

## 🎯 Roadmap

### Próximas Funcionalidades
- [ ] Sistema de notificaciones en tiempo real
- [ ] Chat entre usuarios
- [ ] Estadísticas más avanzadas con gráficos
- [ ] Sistema de torneos automáticos
- [ ] Integración con APIs de fútbol externas
- [ ] Aplicación móvil
- [ ] Sistema de pagos real

### Optimizaciones Técnicas
- [ ] Cache de consultas frecuentes
- [ ] Optimización de consultas SQL
- [ ] Implementación de WebSockets
- [ ] API GraphQL
- [ ] Containerización con Docker

---

**PlayLiga** - Desarrollado con ❤️ y Django
