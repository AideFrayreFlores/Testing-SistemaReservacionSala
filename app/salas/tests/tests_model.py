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

        self.assertEqual(
            error.exception.message_dict['capacidad'],
            ['Asegúrese de que este valor sea mayor o igual a 1.']
        )

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

    def test_ubicacion_es_requerida(self):
        sala = Sala(
            nombre='Sala D',
            capacidad=4,
            ubicacion='',
            activa=True
        )

        with self.assertRaises(ValidationError) as error:
            sala.full_clean()

        self.assertEqual(
            error.exception.message_dict['ubicacion'],
            ['Este campo no puede estar en blanco.']
        )

    def test_activa_por_defecto_es_true(self):
        sala = Sala.objects.create(
            nombre='Sala D',
            capacidad=4,
            ubicacion='Biblioteca, planta baja'
        )
        self.assertTrue(sala.activa)

    def test_nombre_maximo_100_caracteres_valido(self):
        sala = Sala(
            nombre='A' * 100,
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )
        sala.full_clean()
        sala.save()
        self.assertEqual(Sala.objects.count(), 5)

    def test_capacidad_minimo_1_valido(self):
        sala = Sala(
            nombre='Sala D',
            capacidad=1,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )
        sala.full_clean()
        sala.save()
        self.assertEqual(Sala.objects.count(), 5)

    def test_ubicacion_maximo_200_caracteres_valido(self):
        sala = Sala(
            nombre='Sala D',
            capacidad=4,
            ubicacion='A' * 200,
            activa=True
        )
        sala.full_clean()
        sala.save()
        self.assertEqual(Sala.objects.count(), 5)

    def test_ubicacion_mayor_200_caracteres(self):
        sala = Sala(
            nombre='Sala D',
            capacidad=4,
            ubicacion='A' * 201,
            activa=True
        )

        with self.assertRaises(ValidationError) as error:
            sala.full_clean()

        self.assertEqual(
            error.exception.message_dict['ubicacion'],
            ['Asegúrese de que este valor tenga como máximo 200 '
             'caracteres (tiene 201).']
        )

    def test_capacidad_es_requerida(self):
        sala = Sala(
            nombre='Sala D',
            capacidad=None,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )

        with self.assertRaises(ValidationError) as error:
            sala.full_clean()

        self.assertEqual(
            error.exception.message_dict['capacidad'],
            ['Este campo no puede ser nulo.']
        )

    def test_capacidad_negativa_no_permitida(self):
        sala = Sala(
            nombre='Sala D',
            capacidad=-1,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )

        with self.assertRaises(ValidationError) as error:
            sala.full_clean()

        self.assertIn(
            'Asegúrese de que este valor sea mayor o igual a 1.',
            error.exception.message_dict['capacidad']
        )

    def test_sala_a_capacidad_inicial(self):
        sala_a = Sala.objects.get(nombre='Sala A')
        self.assertEqual(sala_a.capacidad, 4)

    def test_sala_mantenimiento_inactiva_inicial(self):
        sala_mant = Sala.objects.get(nombre='Sala de mantenimiento')
        self.assertFalse(sala_mant.activa)
