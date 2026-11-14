from django.test import TestCase
from django.core.exceptions import ValidationError
from salas.models import Sala


class TestSala(TestCase):

    def test_guarda_sala(self):
        Sala.objects.create(
            nombre='Sala D',
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )
        self.assertEqual(Sala.objects.count(), 5)

    def test_existen_cuatro_salas_iniciales(self):
        self.assertEqual(Sala.objects.count(), 4)

    def test_return_object_sala(self):
        sala = Sala.objects.create(
            nombre='Sala D',
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )
        self.assertEqual(str(sala), 'Sala D')

    def test_capacidad_no_acepta_cero(self):
        sala = Sala(
            nombre='Sala D',
            capacidad=0,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )

        with self.assertRaises(ValidationError) as error:
            sala.full_clean()

        self.assertIn('capacidad', error.exception.message_dict)
