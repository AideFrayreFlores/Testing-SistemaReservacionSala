from datetime import date, time
from django.test import TestCase
from salas.models import Sala
from reservaciones.forms import ReservacionForm


class TestFormReservacion(TestCase):

    def setUp(self):
        self.sala = Sala.objects.create(
            nombre='Sala D',
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )
        self.data = {
            'sala': self.sala.id,
            'fecha': date.today(),
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0),
            'asistentes': 3,
            'proposito': 'Estudio grupal para examen'
        }

    def test_reservacion_form_valido(self):
        form = ReservacionForm(data=self.data)
        self.assertTrue(form.is_valid())
