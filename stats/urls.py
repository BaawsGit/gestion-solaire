# stats/urls.py
from django.urls import path
from . import views

app_name = 'stats'

urlpatterns = [
    path('dashboard/', views.statistics_dashboard, name='dashboard'),
    path('export/', views.export_statistics, name='export'),
    path('export/json/', views.export_statistics, name='export_json'),  # Gardez ce nom
    path('export/excel/', views.export_excel, name='export_excel'),  # Gardez ce nom
]