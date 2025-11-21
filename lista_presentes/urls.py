"""
URL configuration for lista_presentes project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pwa.urls')),  # PWA manifest e service worker
    path('', include('presentes.urls')),  # URLs do app presentes
]

# Servir arquivos de mídia (desenvolvimento e produção)
# IMPORTANTE: Em produção, idealmente usar S3 ou CDN, mas para Render.com free tier isso funciona
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Servir arquivos estáticos em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Error handlers customizados para produção
handler500 = 'presentes.error_handlers.handler500'
handler404 = 'presentes.error_handlers.handler404'
