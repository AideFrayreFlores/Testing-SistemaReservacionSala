import json
from datetime import date, datetime, time, timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from reservaciones.models import Reservacion
from salas.models import Sala

PROPOSITO = 'Aceptación HU-02 CA-09 fuera del periodo'


class TestComandoPrepararReservaCa09(TestCase):

    def setUp(self):
        self.usuario = User.objects.get(username='alumno1')
        self.sala = Sala.objects.get(nombre='Sala A')

    def _ejecutar(self, **options):
        salida = StringIO()
        call_command('preparar_reserva_ca09', stdout=salida, **options)
        return json.loads(salida.getvalue().strip().splitlines()[-1])

    def _crear_otra_reservacion(self):
        return Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito='Reservación real de prueba'
        )

    def test_prepara_una_reserva_vigente_en_30_minutos(self):
        ahora = timezone.make_aware(datetime(2026, 11, 17, 10, 0))
        with patch('django.utils.timezone.localtime', return_value=ahora):
            datos = self._ejecutar()
        reservacion = Reservacion.objects.get(pk=datos['id'])
        self.assertEqual(reservacion.usuario, self.usuario)
        self.assertEqual(reservacion.sala, self.sala)
        self.assertEqual(reservacion.estado, 'VIGENTE')
        self.assertEqual(reservacion.proposito, PROPOSITO)
        inicio = timezone.make_aware(
            datetime.combine(reservacion.fecha, reservacion.hora_inicio)
        )
        self.assertEqual(inicio, ahora + timedelta(minutes=30))

    def test_preparar_de_nuevo_reemplaza_solo_su_fila(self):
        otra = self._crear_otra_reservacion()
        self._ejecutar()
        self._ejecutar()
        self.assertEqual(
            Reservacion.objects.filter(proposito=PROPOSITO).count(),
            1
        )
        self.assertTrue(Reservacion.objects.filter(pk=otra.id).exists())

    def test_limpiar_elimina_solo_la_fila_indicada(self):
        datos = self._ejecutar()
        otra = self._crear_otra_reservacion()
        self._ejecutar(limpiar=datos['id'])
        self.assertFalse(
            Reservacion.objects.filter(pk=datos['id']).exists()
        )
        self.assertTrue(Reservacion.objects.filter(pk=otra.id).exists())

    def test_limpiar_es_idempotente(self):
        datos = self._ejecutar()
        self._ejecutar(limpiar=datos['id'])
        self._ejecutar(limpiar=datos['id'])
        self.assertFalse(
            Reservacion.objects.filter(pk=datos['id']).exists()
        )

    def test_limpiar_rechaza_otra_reservacion(self):
        otra = self._crear_otra_reservacion()
        with self.assertRaises(CommandError):
            self._ejecutar(limpiar=otra.id)
        self.assertTrue(Reservacion.objects.filter(pk=otra.id).exists())

    def test_falla_si_falta_el_usuario_de_prueba(self):
        self.usuario.delete()
        with self.assertRaises(CommandError):
            self._ejecutar()

    def test_ajusta_hora_fin_si_cruza_medianoche(self):
        ahora = timezone.make_aware(datetime(2026, 11, 17, 22, 45))
        with patch('django.utils.timezone.localtime', return_value=ahora):
            datos = self._ejecutar()
        self.assertEqual(datos['hora_fin'], '23:59')

    def test_falla_si_falta_la_sala_de_prueba(self):
        self.sala.delete()
        with self.assertRaisesMessage(
            CommandError, 'Falta la sala de prueba Sala A.'
        ):
            self._ejecutar()
