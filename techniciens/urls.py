from django.urls import path
from . import views

urlpatterns = [
    # Techniciens
    path('', views.technicien_list, name='technicien_list'),
    path('creer/', views.technicien_create, name='technicien_create'),
    path('<int:pk>/', views.technicien_detail, name='technicien_detail'),
    path('<int:pk>/modifier/', views.technicien_update, name='technicien_update'),
    path('<int:pk>/supprimer/', views.technicien_delete, name='technicien_delete'),
]