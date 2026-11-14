from datetime import date, time
from django.test import TestCase
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
