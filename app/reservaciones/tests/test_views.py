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
            password='usuario123_'
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
        self.assertRedirects(
            response,
            '/usuarios/login?next=/reservaciones/nueva',
            fetch_redirect_response=False
        )

    def test_template_correcto_nueva_reservacion(self):
        self.client.login(username='usuario1', password='usuario123_')
        response = self.client.get('/reservaciones/nueva')
        self.assertTemplateUsed(
            response,
            'reservaciones/nueva_reservacion.html'
        )

    def test_nueva_reservacion_response(self):
        self.client.login(username='usuario1', password='usuario123_')
        response = self.client.get('/reservaciones/nueva')
        self.assertEqual(response.status_code, 200)

    def test_nombre_url_nueva_reservacion_response(self):
        self.client.login(username='usuario1', password='usuario123_')
        response_url = self.client.get(reverse('nueva_reservacion'))
        self.assertEqual(response_url.status_code, 200)

    def test_titulo_se_encuentra_en_el_template_nueva_reservacion(self):
        self.client.login(username='usuario1', password='usuario123_')
        response = self.client.get('/reservaciones/nueva')
        titulo = '<title>Nueva reservación</title>'
        self.assertInHTML(titulo, response.content.decode('utf-8'))

    def test_crear_reservacion_post_valido_guarda_registro(self):
        self.client.login(username='usuario1', password='usuario123_')
        self.client.post('/reservaciones/nueva', data=self.datos)
        self.assertEqual(Reservacion.objects.count(), 1)

    def test_crear_reservacion_post_valido_estado_vigente(self):
        self.client.login(username='usuario1', password='usuario123_')
        self.client.post('/reservaciones/nueva', data=self.datos)
        self.assertEqual(Reservacion.objects.first().estado, 'VIGENTE')

    def test_crear_reservacion_post_valido_redirige(self):
        self.client.login(username='usuario1', password='usuario123_')
        response = self.client.post('/reservaciones/nueva', data=self.datos)
        self.assertRedirects(
            response,
            '/reservaciones/',
            fetch_redirect_response=False
        )

    def test_crear_reservacion_post_valido_muestra_mensaje(self):
        self.client.login(username='usuario1', password='usuario123_')
        response = self.client.post(
            '/reservaciones/nueva',
            data=self.datos,
            follow=True
        )
        self.assertContains(
            response,
            'Reservación registrada exitosamente.'
        )

    def test_crear_reservacion_post_traslape_status_200(self):
        self.client.login(username='usuario1', password='usuario123_')
        self.client.post('/reservaciones/nueva', data=self.datos)
        self.datos['hora_inicio'] = time(10, 30)
        self.datos['hora_fin'] = time(11, 30)
        response = self.client.post('/reservaciones/nueva', data=self.datos)
        self.assertEqual(response.status_code, 200)

    def test_crear_reservacion_post_traslape_no_guarda_duplicada(self):
        self.client.login(username='usuario1', password='usuario123_')
        self.client.post('/reservaciones/nueva', data=self.datos)
        self.datos['hora_inicio'] = time(10, 30)
        self.datos['hora_fin'] = time(11, 30)
        self.client.post('/reservaciones/nueva', data=self.datos)
        self.assertEqual(Reservacion.objects.count(), 1)

    def test_crear_reservacion_post_traslape_muestra_error(self):
        self.client.login(username='usuario1', password='usuario123_')
        self.client.post('/reservaciones/nueva', data=self.datos)
        self.datos['hora_inicio'] = time(10, 30)
        self.datos['hora_fin'] = time(11, 30)
        response = self.client.post('/reservaciones/nueva', data=self.datos)
        self.assertContains(
            response,
            'La sala no está disponible en el horario solicitado.'
        )

    def test_crear_reservacion_post_invalido_status_200(self):
        self.client.login(username='usuario1', password='usuario123_')
        self.datos['asistentes'] = 10
        response = self.client.post('/reservaciones/nueva', data=self.datos)
        self.assertEqual(response.status_code, 200)

    def test_crear_reservacion_post_invalido_no_guarda(self):
        self.client.login(username='usuario1', password='usuario123_')
        self.datos['asistentes'] = 10
        self.client.post('/reservaciones/nueva', data=self.datos)
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_crear_reservacion_post_invalido_muestra_error(self):
        self.client.login(username='usuario1', password='usuario123_')
        self.datos['asistentes'] = 10
        response = self.client.post('/reservaciones/nueva', data=self.datos)
        self.assertContains(
            response,
            'El número de asistentes supera la capacidad de la sala.'
        )

    def test_crear_reservacion_post_invalido_conserva_datos(self):
        self.client.login(username='usuario1', password='usuario123_')
        self.datos['asistentes'] = 10
        response = self.client.post('/reservaciones/nueva', data=self.datos)
        self.assertContains(response, 'Estudio grupal para examen')

    def test_listar_reservaciones_redirige_si_anonimo(self):
        response = self.client.get('/reservaciones/')
        self.assertRedirects(
            response,
            '/usuarios/login?next=/reservaciones/',
            fetch_redirect_response=False
        )

    def test_listar_reservaciones_autenticado_status_200(self):
        self.client.login(username='usuario1', password='usuario123_')
        response = self.client.get('/reservaciones/')
        self.assertEqual(response.status_code, 200)

    def test_listar_reservaciones_autenticado_usa_template_correcto(self):
        self.client.login(username='usuario1', password='usuario123_')
        response = self.client.get('/reservaciones/')
        self.assertTemplateUsed(
            response,
            'reservaciones/lista_reservaciones.html'
        )


class TestViewsCancelacion(TestCase):

    def test_impedir_cancelacion_anonima(self):
        url = '/reservaciones/cancelar/1'
        response = self.client.post(url)
        self.assertRedirects(
            response,
            f'/usuarios/login?next={url}',
            fetch_redirect_response=False
        )
