from django.db import models
from django.contrib.auth.models import User


class Technicien(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Lien avec un utilisateur Django"
    )
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    email = models.EmailField()
    photo = models.ImageField(
        upload_to='techniciens_photos/',
        blank=True,
        null=True,
        default='techniciens_photos/default.jpg'
    )

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Technicien"
        verbose_name_plural = "Techniciens"