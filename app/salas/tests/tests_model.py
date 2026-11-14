from django.test import TestCase
from salas.models import Sala


class TestSala(TestCase):

    def test_guarda_sala(self):
        Sala.objects.create(
            nombre='Sala A',
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )
        self.assertEqual(Sala.objects.count(), 1)

    def test_existen_cuatro_salas_iniciales(self):
        self.assertEqual(Sala.objects.count(), 4)
