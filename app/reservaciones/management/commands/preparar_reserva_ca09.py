"""Datos de apoyo aislados para el escenario CA-09.

Crea una sola reservación de alumno1 en Sala A que inicia 30 minutos después
del momento de la ejecución, sin congelar el reloj. El comando nunca borra
reservaciones ajenas: reemplaza únicamente las filas que llevan su propósito
de prueba y `--limpiar ID` elimina solo el identificador indicado, validando
que pertenezca a este fixture.
"""

import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from reservaciones.models import Reservacion
from salas.models import Sala

USUARIO = 'alumno1'
SALA = 'Sala A'
PROPOSITO = 'Aceptación HU-02 CA-09 fuera del periodo'
ANTICIPACION = timedelta(minutes=30)
DURACION = timedelta(hours=1)


class Command(BaseCommand):
    help = (
        'Prepara la reservación de CA-09 (alumno1, inicio en 30 minutos) '
        'y elimina solo esa fila con --limpiar ID.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            type=int,
            metavar='ID',
            help='Elimina la reservación de CA-09 con el identificador ID.'
        )

    def handle(self, *args, **options):
        if options['limpiar'] is not None:
            self.limpiar(options['limpiar'])
        else:
            self.stdout.write(json.dumps(self.preparar()))

    def preparar(self):
        usuario = self.obtener_usuario()
        sala = self.obtener_sala()
        Reservacion.objects.filter(
            usuario=usuario,
            proposito=PROPOSITO
        ).delete()
        inicio = timezone.localtime() + ANTICIPACION
        fin = inicio + DURACION
        if fin.date() != inicio.date():
            fin = inicio.replace(hour=23, minute=59)
        reservacion = Reservacion.objects.create(
            usuario=usuario,
            sala=sala,
            fecha=inicio.date(),
            hora_inicio=inicio.time().replace(second=0, microsecond=0),
            hora_fin=fin.time().replace(second=0, microsecond=0),
            asistentes=2,
            proposito=PROPOSITO
        )
        return {
            'id': reservacion.id,
            'fecha': reservacion.fecha.isoformat(),
            'hora_inicio': reservacion.hora_inicio.strftime('%H:%M'),
            'hora_fin': reservacion.hora_fin.strftime('%H:%M'),
            'proposito': reservacion.proposito,
        }

    def limpiar(self, reservacion_id):
        reservacion = Reservacion.objects.filter(pk=reservacion_id).first()
        if reservacion is None:
            self.stdout.write(json.dumps({'eliminada': reservacion_id}))
            return
        if (reservacion.usuario.username != USUARIO
                or reservacion.proposito != PROPOSITO):
            raise CommandError(
                'La reservación indicada no corresponde a la preparada '
                'por este comando.'
            )
        reservacion.delete()
        self.stdout.write(json.dumps({'eliminada': reservacion_id}))

    def obtener_usuario(self):
        try:
            return User.objects.get(username=USUARIO)
        except User.DoesNotExist:
            raise CommandError(
                f'Falta el usuario de prueba {USUARIO}.'
            ) from None

    def obtener_sala(self):
        try:
            return Sala.objects.get(nombre=SALA)
        except Sala.DoesNotExist:
            raise CommandError(
                f'Falta la sala de prueba {SALA}.'
            ) from None
