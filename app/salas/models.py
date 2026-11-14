from django.core.validators import MinValueValidator
from django.db import models


class Sala(models.Model):
    nombre = models.CharField(max_length=100)
    capacidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    ubicacion = models.CharField(max_length=200)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
