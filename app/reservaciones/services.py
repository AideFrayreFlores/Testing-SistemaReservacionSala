from datetime import datetime
from django.core.exceptions import ValidationError
from reservaciones.models import Reservacion


def registrar_reservacion(
    usuario,
    sala,
    fecha,
    hora_inicio,
    hora_fin,
    asistentes,
    proposito
):
    inicio_dt = datetime.combine(fecha, hora_inicio)
    fin_dt = datetime.combine(fecha, hora_fin)
    duracion_minutos = (fin_dt - inicio_dt).total_seconds() / 60

    if duracion_minutos < 30 or duracion_minutos > 120:
        raise ValidationError(
            'La duración de la reservación debe ser de entre 30 minutos y 2 horas.'
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
