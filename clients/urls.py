from django.urls import path
from . import views

urlpatterns = [
    # Clients
    path('', views.client_list, name='client_list'),
    path('creer/', views.client_create, name='client_create'),
    path('<int:pk>/', views.client_detail, name='client_detail'),
    path('<int:pk>/modifier/', views.client_update, name='client_update'),
    path('<int:pk>/supprimer/', views.client_delete, name='client_delete'),

    # Fournisseurs
    path('fournisseurs/', views.fournisseur_list, name='fournisseur_list'),
    path('fournisseurs/<int:pk>/', views.fournisseur_detail, name='fournisseur_detail'),  # NOUVEAU
    path('fournisseurs/<int:pk>/modifier/', views.fournisseur_update, name='fournisseur_update'),  # NOUVEAU
    path('fournisseurs/<int:pk>/supprimer/', views.fournisseur_delete, name='fournisseur_delete'),  # NOUVELLE LIGNE

    # AJAX
    path('ajax/create-fournisseur/', views.ajax_create_fournisseur, name='ajax_create_fournisseur'),
]