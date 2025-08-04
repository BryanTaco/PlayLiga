from django.contrib import admin
from django.urls import path, include
from mitorneo import views as torneo_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', torneo_views.home),  # Redirige al login
    path('torneo/', include('mitorneo.urls')),  # urls propias de la app
]