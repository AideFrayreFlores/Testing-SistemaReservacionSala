from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from salas.models import Sala
from reservaciones.models import Reservacion


def registrar_reservacion(datos):
    usuario = datos['usuario']
    sala = datos['sala']
    fecha = datos['fecha']
    hora_inicio = datos['hora_inicio']
    hora_fin = datos['hora_fin']
    asistentes = datos['asistentes']
    proposito = datos['proposito']

    inicio_dt = datetime.combine(fecha, hora_inicio)
    fin_dt = datetime.combine(fecha, hora_fin)
    duracion_minutos = (fin_dt - inicio_dt).total_seconds() / 60

    if duracion_minutos < 30 or duracion_minutos > 120:
        raise ValidationError(
            'La duración de la reservación debe ser de '
            'entre 30 minutos y 2 horas.'
        )

    with transaction.atomic():
        Sala.objects.select_for_update().get(pk=sala.pk)

        traslape = Reservacion.objects.filter(
            sala=sala,
            fecha=fecha,
            estado='VIGENTE',
            hora_inicio__lt=hora_fin,
            hora_fin__gt=hora_inicio
        ).exists()

        if traslape:
            raise ValidationError(
                'La sala no está disponible en el horario solicitado.'
            )

        return Reservacion.objects.create(
            usuario=usuario,
            sala=sala,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            asistentes=asistentes,
            proposito=proposito
        )


def cancelar_reservacion(reservacion_id, usuario, ahora=None):
    reservacion = Reservacion.objects.get(pk=reservacion_id)
    if reservacion.usuario_id != getattr(usuario, 'pk', None):
        raise ValidationError(
            'No tienes permiso para cancelar esta reservación.'
        )
    reservacion.estado = 'CANCELADA'
    reservacion.fecha_cancelacion = ahora or timezone.now()
    reservacion.save(update_fields=['estado', 'fecha_cancelacion'])
    return reservacion
