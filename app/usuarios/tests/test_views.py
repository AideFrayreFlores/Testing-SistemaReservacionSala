from django.test import TestCase


class TestViews(TestCase):

    def test_login_response(self):
        response = self.client.get('/usuarios/login')
        self.assertEqual(response.status_code, 200)
