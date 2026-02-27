from django.urls import path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    # URLs temporaires pour les autres sections
    path('techniciens/', views.technicien_list_view, name='technicien_list'),
    path('interventions/', RedirectView.as_view(url='/interventions/', permanent=False), name='intervention_list'),
]