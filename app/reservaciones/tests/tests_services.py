from datetime import date, time
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from salas.models import Sala
from reservaciones.services import registrar_reservacion


class TestServicioReservacion(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='usuario1',
            password='Password123!'
        )
        self.sala = Sala.objects.create(
            nombre='Sala D',
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )
        self.datos = {
            'usuario': self.usuario,
            'sala': self.sala,
            'fecha': date.today(),
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0),
            'asistentes': 3,
            'proposito': 'Estudio grupal para examen'
        }

    def test_duracion_menor_a_30_minutos_invalida(self):
        self.datos['hora_inicio'] = time(10, 0)
        self.datos['hora_fin'] = time(10, 29)
        with self.assertRaises(ValidationError) as error:
            registrar_reservacion(**self.datos)
        self.assertEqual(
            error.exception.messages,
            ['La duración de la reservación debe ser de entre 30 minutos y 2 horas.']
        )

