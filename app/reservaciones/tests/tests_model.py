from datetime import date, time
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from salas.models import Sala
from reservaciones.models import Reservacion


class TestReservacion(TestCase):

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

    def test_crear_reservacion_valida_estado_vigente(self):
        reservacion = Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=3,
            proposito='Estudio grupal para examen'
        )
        self.assertEqual(Reservacion.objects.count(), 1)
        self.assertEqual(reservacion.estado, 'VIGENTE')
        self.assertIsNotNone(reservacion.fecha_creacion)
        self.assertIsNone(reservacion.fecha_cancelacion)

    def test_return_object_reservacion(self):
        reservacion = Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date(2026, 11, 20),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=3,
            proposito='Estudio grupal para examen'
        )
        self.assertEqual(
            str(reservacion),
            'usuario1 - Sala D - 2026-11-20 - 10:00:00 a 11:00:00 - 3'
        )

    def test_asistentes_no_acepta_cero(self):
        reservacion = Reservacion(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=0,
            proposito='Estudio grupal para examen'
        )

        with self.assertRaises(ValidationError) as error:
            reservacion.full_clean()

        self.assertEqual(
            error.exception.message_dict['asistentes'],
            ['Asegúrese de que este valor sea mayor o igual a 1.']
        )

    def test_proposito_es_requerido(self):
        reservacion = Reservacion(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=3,
            proposito=''
        )

        with self.assertRaises(ValidationError) as error:
            reservacion.full_clean()

        self.assertEqual(
            error.exception.message_dict['proposito'],
            ['Este campo no puede estar en blanco.']
        )

    def test_proposito_mayor_200_caracteres(self):
        reservacion = Reservacion(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=3,
            proposito='A' * 201
        )

        with self.assertRaises(ValidationError) as error:
            reservacion.full_clean()

        self.assertEqual(
            error.exception.message_dict['proposito'],
            ['Asegúrese de que este valor tenga como máximo 200 '
             'caracteres (tiene 201).']
        )

    def test_proposito_menor_10_caracteres(self):
        reservacion = Reservacion(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=3,
            proposito='A' * 9
        )

        with self.assertRaises(ValidationError) as error:
            reservacion.full_clean()

        self.assertEqual(
            error.exception.message_dict['proposito'],
            ['Asegúrese de que este valor tenga como mínimo 10 '
             'caracteres (tiene 9).']
        )

    def test_proposito_minimo_10_caracteres_valido(self):
        reservacion = Reservacion(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=3,
            proposito='A' * 10
        )
        reservacion.full_clean()
        reservacion.save()
        self.assertEqual(Reservacion.objects.count(), 1)

    def test_proposito_maximo_200_caracteres_valido(self):
        reservacion = Reservacion(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=3,
            proposito='A' * 200
        )
        reservacion.full_clean()
        reservacion.save()
        self.assertEqual(Reservacion.objects.count(), 1)

    def test_asistentes_minimo_1_valido(self):
        reservacion = Reservacion(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=1,
            proposito='Estudio grupal para examen'
        )
        reservacion.full_clean()
        reservacion.save()
        self.assertEqual(Reservacion.objects.count(), 1)

    def test_estado_invalido_no_permitido(self):
        reservacion = Reservacion(
            usuario=self.usuario,
            sala=self.sala,
            fecha=date.today(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=3,
            proposito='Estudio grupal para examen',
            estado='FINALIZADA'
        )

        with self.assertRaises(ValidationError) as error:
            reservacion.full_clean()

        self.assertEqual(
            error.exception.message_dict['estado'],
            ["El valor 'FINALIZADA' no es una opción válida."]
        )
