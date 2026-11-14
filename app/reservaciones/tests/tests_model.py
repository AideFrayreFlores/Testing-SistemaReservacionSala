from datetime import date, time
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from salas.models import Sala
from reservaciones.models import Reservacion


class TestReservacion(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='usuario1',
            email='usuario1@correo.com',
            password='Password123!'
        )
        self.sala = Sala.objects.create(
            nombre='Sala D',
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )

    def test_crear_reservacion_valida_estado_vigente(self):
        reservacion = Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=3,
            proposito='Estudio grupal para examen'
        )
        self.assertEqual(Reservacion.objects.count(), 1)
        self.assertEqual(reservacion.estado, 'VIGENTE')
        self.assertIsNotNone(reservacion.fecha_creacion)
        self.assertIsNone(reservacion.fecha_cancelacion)

    def test_return_object_reservacion(self):
        reservacion = Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date(2026, 11, 20),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=3,
            proposito='Estudio grupal para examen'
        )
        self.assertEqual(
            str(reservacion),
            'usuario1 - Sala D - 2026-11-20 - 10:00:00 a 11:00:00 - 3'
        )

    def test_asistentes_no_acepta_cero(self):
        reservacion = Reservacion(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=0,
            proposito='Estudio grupal para examen'
        )

        with self.assertRaises(ValidationError) as error:
            reservacion.full_clean()

        self.assertEqual(
            error.exception.message_dict['asistentes'],
            ['Asegúrese de que este valor sea mayor o igual a 1.']
        )
