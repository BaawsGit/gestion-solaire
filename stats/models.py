# stats/models.py
from django.db import models
from django.utils import timezone


class StatisticCache(models.Model):
    """Cache pour les statistiques calculées"""
    name = models.CharField(max_length=100, unique=True)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "Cache Statistique"
        verbose_name_plural = "Caches Statistiques"
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def is_expired(self):
        return timezone.now() > self.expires_at