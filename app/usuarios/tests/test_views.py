from django.test import TestCase
from django.urls import reverse


class TestViews(TestCase):

    def test_login_response(self):
        response = self.client.get('/usuarios/login')
        self.assertEqual(response.status_code, 200)

    def test_nombre_url_login_response(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_template_correcto_login(self):
        response = self.client.get('/usuarios/login')
        self.assertTemplateUsed(response, 'usuarios/login.html')
