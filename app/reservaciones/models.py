from django.core.validators import MinValueValidator, MinLengthValidator
from django.db import models
from django.contrib.auth.models import User
from salas.models import Sala


class Reservacion(models.Model):
    ESTADOS = [
        ('VIGENTE', 'Vigente'),
        ('CANCELADA', 'Cancelada'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    asistentes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    proposito = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(10)]
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default='VIGENTE'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (
            f'{self.usuario.username} - {self.sala.nombre} - '
            f'{self.fecha} - {self.hora_inicio} a {self.hora_fin} - '
            f'{self.asistentes}'
        )
