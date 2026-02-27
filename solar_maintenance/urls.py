"""
URL configuration for solar_maintenance project.

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
from django.views.generic import RedirectView

urlpatterns = [
    # Redirection de la racine vers le login
    path('', RedirectView.as_view(url='/auth/login/', permanent=False)),
    path('admin/', admin.site.urls),

    # Authentification
    path('auth/', include('authentication.urls')),

    # Dashboard
    path('dashboard/', include('dashboard.urls')),

    # Clients
    path('clients/', include('clients.urls')),  # NOUVEAU

    #Techniciens
    path('techniciens/', include('techniciens.urls')),  # NOUVEAU

    # Interventions
    path('interventions/', include('interventions.urls', namespace='interventions')),

    # Statistiques
    path('stats/', include('stats.urls', namespace='stats')),

    path('reports/', include('reports.urls', namespace='reports')),  # AJOUTER CETTE LIGNE
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Personnalisation du titre de l'administration
admin.site.site_header = "Solar Maintenance Administration"
admin.site.site_title = "Solar Maintenance Admin"
admin.site.index_title = "Bienvenue dans l'administration Solar Maintenance"