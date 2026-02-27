from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('generate/', views.generate_report, name='generate_report'),
    path('<int:pk>/', views.report_detail, name='report_detail'),
    path('<int:pk>/delete/', views.report_delete, name='report_delete'),

    # URLs pour la connexion Ollama
    path('check-ollama/', views.check_ollama_status, name='check_ollama_status'),
    path('test-connection/', views.test_ollama_connection, name='test_connection'),
    # Dans reports/urls.py
    path('config/', views.ollama_config, name='ollama_config'),
]