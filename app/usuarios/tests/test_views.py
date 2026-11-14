from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class TestViews(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='usuario1',
            email='usuario1@correo.com',
            password='Password123!'
        )

    def test_login_response(self):
        response = self.client.get('/usuarios/login')
        self.assertEqual(response.status_code, 200)

    def test_nombre_url_login_response(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_template_correcto_login(self):
        response = self.client.get('/usuarios/login')
        self.assertTemplateUsed(response, 'usuarios/login.html')

    def test_titulo_se_encuentra_en_el_template(self):
        response = self.client.get('/usuarios/login')
        titulo = '<title>Iniciar sesión</title>'
        self.assertInHTML(titulo, response.rendered_content)

    def test_login_credenciales_invalidas_muestra_error(self):
        response = self.client.post(
            '/usuarios/login',
            data={'username': 'invalido', 'password': 'incorrecta'}
        )
        mensaje = (
            'Por favor introduzca un nombre de usuario y contraseña correctos.'
        )
        self.assertIn(mensaje, response.rendered_content)

    def test_login_credenciales_validas_redirige(self):
        response = self.client.post(
            '/usuarios/login',
            data={'username': 'usuario1', 'password': 'Password123!'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/reservaciones/')
