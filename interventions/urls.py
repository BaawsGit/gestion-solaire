from django.urls import path
from . import views
from . import views_calendar  # Importer les nouvelles vues
from . import views_pdf  # Ajouter cette ligne

app_name = 'interventions'

urlpatterns = [
    path('', views.intervention_list, name='list'),
    path('creer/', views.intervention_create, name='create'),
    path('<int:pk>/', views.intervention_detail, name='detail'),
    path('<int:pk>/modifier/', views.intervention_update, name='update'),
    path('<int:pk>/supprimer/', views.intervention_delete, name='delete'),
    # API pour récupérer le fournisseur d'un client
    path('api/client/<int:client_id>/fournisseur/', views.get_client_fournisseur, name='client_fournisseur_api'),

    # Nouvelles URLs pour le calendrier
    path('calendar/', views_calendar.calendar_view, name='calendar'),
    path('calendar/events/', views_calendar.calendar_events, name='calendar_events'),

    # Ajouter cette ligne :
    path('<int:pk>/pdf/', views_pdf.intervention_pdf, name='pdf'),

    # ... autres URLs ...
    path('api/client/<int:client_id>/prix/', views.get_prix_intervention_api, name='prix_intervention_api'),
]