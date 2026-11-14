from datetime import date, time
from django.contrib.auth.models import User
from django.test import TestCase
from salas.models import Sala


class TestViewsReservacion(TestCase):

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
        self.datos = {
            'sala': self.sala.id,
            'fecha': date.today(),
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0),
            'asistentes': 3,
            'proposito': 'Estudio grupal para examen'
        }

    def test_redirige_si_no_inicio_sesion_nueva_reservacion(self):
        response = self.client.get('/reservaciones/nueva')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            '/usuarios/login?next=/reservaciones/nueva'
        )

    def test_template_correcto_nueva_reservacion(self):
        self.client.login(username='usuario1', password='Password123!')
        response = self.client.get('/reservaciones/nueva')
        self.assertTemplateUsed(
            response,
            'reservaciones/nueva_reservacion.html'
        )


