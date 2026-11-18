from datetime import date, datetime, time, timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
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

    @classmethod
    def setUpTestData(cls):
        cls.usuario = User.objects.create_user(username='usuario1')
        cls.otro_usuario = User.objects.create_user(username='usuario2')
        cls.sala = Sala.objects.create(
            nombre='Sala D',
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )
        cls.reservacion = Reservacion.objects.create(
            usuario=cls.otro_usuario,
            sala=cls.sala,
            fecha=timezone.localdate() + timedelta(days=2),
            hora_inicio=time(14, 0),
            hora_fin=time(15, 0),
            asistentes=2,
            proposito='Propósito privado del propietario'
        )
        cls.url = reverse('cancelar_reservacion', args=[cls.reservacion.pk])

    def test_impedir_cancelacion_anonima(self):
        url = '/reservaciones/cancelar/1'
        response = self.client.post(url)
        self.assertRedirects(
            response,
            f'/usuarios/login?next={url}',
            fetch_redirect_response=False
        )

    def test_impedir_cancelacion_manipulada_de_reservacion_ajena(self):
        self.client.force_login(self.usuario)
        response = self.client.post(self.url, follow=True)
        self.assertContains(
            response, 'No tienes permiso para cancelar esta reservación.'
        )

    def test_cancelacion_ajena_conserva_estado_vigente(self):
        self.client.force_login(self.usuario)
        self.client.post(self.url)
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, 'VIGENTE')

    def test_rechazo_no_muestra_proposito_de_reservacion_ajena(self):
        self.client.force_login(self.usuario)
        response = self.client.post(self.url, follow=True)
        self.assertNotContains(response, self.reservacion.proposito)

    def test_get_no_cancela_reservacion(self):
        self.client.force_login(self.otro_usuario)
        response = self.client.get(self.url)
        self.reservacion.refresh_from_db()
        self.assertEqual(
            (response.status_code, self.reservacion.estado),
            (405, 'VIGENTE')
        )

    def test_post_sin_csrf_no_cancela_reservacion(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.otro_usuario)
        response = cliente.post(self.url)
        self.reservacion.refresh_from_db()
        self.assertEqual(
            (response.status_code, self.reservacion.estado),
            (403, 'VIGENTE')
        )

    def test_post_con_csrf_cancela_reservacion(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.otro_usuario)
        cliente.get(reverse('lista_reservaciones'))
        token = cliente.cookies['csrftoken'].value
        response = cliente.post(self.url, {'csrfmiddlewaretoken': token})
        self.reservacion.refresh_from_db()
        self.assertEqual(
            (response.status_code, self.reservacion.estado),
            (302, 'CANCELADA')
        )

    def test_cancelacion_propia_muestra_mensaje_de_exito(self):
        self.client.force_login(self.otro_usuario)
        response = self.client.post(self.url, follow=True)
        self.assertContains(response, 'Reservación cancelada exitosamente.')

    def test_lista_muestra_accion_de_cancelar_reservacion_vigente(self):
        self.client.force_login(self.otro_usuario)
        response = self.client.get(reverse('lista_reservaciones'))
        self.assertContains(response, f'action="{self.url}"')

    def test_lista_avisa_que_el_periodo_de_cancelacion_concluyo(self):
        self.client.force_login(self.otro_usuario)
        inicio = timezone.make_aware(datetime.combine(
            self.reservacion.fecha, self.reservacion.hora_inicio
        ))
        with patch(
            'django.utils.timezone.now',
            return_value=inicio - timedelta(minutes=30)
        ):
            response = self.client.get(reverse('lista_reservaciones'))
        self.assertContains(
            response, 'El periodo de cancelación ha concluido.'
        )

    def test_lista_muestra_fecha_y_hora_de_cancelacion(self):
        self.client.force_login(self.otro_usuario)
        self.reservacion.estado = 'CANCELADA'
        self.reservacion.fecha_cancelacion = timezone.make_aware(
            datetime(2026, 11, 17, 15, 30)
        )
        self.reservacion.save(update_fields=['estado', 'fecha_cancelacion'])
        response = self.client.get(reverse('lista_reservaciones'))
        self.assertContains(response, '17/11/2026 15:30')

    def test_lista_oculta_accion_si_concluyo_el_periodo(self):
        self.client.force_login(self.otro_usuario)
        inicio = timezone.make_aware(datetime.combine(
            self.reservacion.fecha, self.reservacion.hora_inicio
        ))
        with patch(
            'django.utils.timezone.now',
            return_value=inicio - timedelta(minutes=60)
        ):
            response = self.client.get(reverse('lista_reservaciones'))
        self.assertNotContains(response, f'action="{self.url}"')

    def test_lista_oculta_accion_de_reservacion_cancelada(self):
        self.client.force_login(self.otro_usuario)
        self.client.post(self.url)
        response = self.client.get(reverse('lista_reservaciones'))
        self.assertNotContains(response, f'action="{self.url}"')

    def test_cancelar_conserva_reservacion_en_el_historial(self):
        self.client.force_login(self.otro_usuario)
        response = self.client.post(self.url, follow=True)
        self.assertContains(
            response, '<span class="badge-cancelada">CANCELADA</span>',
            html=True
        )
