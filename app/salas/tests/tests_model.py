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

    def test_nombre_es_requerido(self):
        sala = Sala(
            nombre='',
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )

        with self.assertRaises(ValidationError) as error:
            sala.full_clean()

        self.assertEqual(
            error.exception.message_dict['nombre'],
            ['Este campo no puede estar en blanco.']
        )

    def test_nombre_mayor_100_caracteres(self):
        sala = Sala(
            nombre='A' * 101,
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )

        with self.assertRaises(ValidationError) as error:
            sala.full_clean()

        self.assertEqual(
            error.exception.message_dict['nombre'],
            ['Asegúrese de que este valor tenga como máximo 100 '
             'caracteres (tiene 101).']
        )
