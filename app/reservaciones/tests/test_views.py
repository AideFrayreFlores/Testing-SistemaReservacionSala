from datetime import date, time
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from salas.models import Sala
from reservaciones.models import Reservacion


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

    def test_nueva_reservacion_response_y_nombre_url(self):
        self.client.login(username='usuario1', password='Password123!')
        response = self.client.get('/reservaciones/nueva')
        response_url = self.client.get(reverse('nueva_reservacion'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_url.status_code, 200)

    def test_titulo_se_encuentra_en_el_template_nueva_reservacion(self):
        self.client.login(username='usuario1', password='Password123!')
        response = self.client.get('/reservaciones/nueva')
        titulo = '<title>Nueva reservación</title>'
        self.assertInHTML(titulo, response.content.decode('utf-8'))

    def test_crear_reservacion_post_valido_redirige_y_muestra_mensaje(self):
        self.client.login(username='usuario1', password='Password123!')
        response = self.client.post(
            '/reservaciones/nueva',
            data=self.datos,
            follow=True
        )
        self.assertEqual(Reservacion.objects.count(), 1)
        self.assertEqual(Reservacion.objects.first().estado, 'VIGENTE')
        self.assertRedirects(response, '/reservaciones/')
        self.assertContains(
            response,
            'Reservación registrada exitosamente.'
        )

    def test_crear_reservacion_post_traslape_muestra_error_y_no_guarda(self):
        self.client.login(username='usuario1', password='Password123!')
        self.client.post('/reservaciones/nueva', data=self.datos)
        self.datos['hora_inicio'] = time(10, 30)
        self.datos['hora_fin'] = time(11, 30)
        response = self.client.post('/reservaciones/nueva', data=self.datos)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 1)
        self.assertContains(
            response,
            'La sala no está disponible en el horario solicitado.'
        )

    def test_crear_reservacion_post_invalido_conserva_datos_y_no_guarda(self):
        self.client.login(username='usuario1', password='Password123!')
        self.datos['asistentes'] = 10
        response = self.client.post('/reservaciones/nueva', data=self.datos)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 0)
        self.assertContains(
            response,
            'El número de asistentes supera la capacidad de la sala.'
        )
        self.assertContains(response, 'Estudio grupal para examen')

    def test_listar_reservaciones_anonimo_y_autenticado(self):
        response_anon = self.client.get('/reservaciones/')
        self.assertEqual(response_anon.status_code, 302)
        self.assertEqual(
            response_anon.url,
            '/usuarios/login?next=/reservaciones/'
        )

        self.client.login(username='usuario1', password='Password123!')
        response = self.client.get('/reservaciones/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'reservaciones/lista_reservaciones.html'
        )







