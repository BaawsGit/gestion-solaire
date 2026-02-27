from django.contrib import admin
from .models import Technicien

@admin.register(Technicien)
class TechnicienAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'telephone', 'email')
    search_fields = ('nom', 'email', 'telephone')