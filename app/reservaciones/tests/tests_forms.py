from datetime import date, time, timedelta
from django.test import TestCase
from salas.models import Sala
from reservaciones.forms import ReservacionForm


class TestFormReservacion(TestCase):

    def setUp(self):
        self.sala = Sala.objects.create(
            nombre='Sala D',
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )
        self.data = {
            'sala': self.sala.id,
            'fecha': date.today(),
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0),
            'asistentes': 3,
            'proposito': 'Estudio grupal para examen'
        }

    def test_reservacion_form_valido(self):
        form = ReservacionForm(data=self.data)
        self.assertTrue(form.is_valid())

    def test_proposito_menor_10_caracteres_invalido(self):
        self.data['proposito'] = '   corto   '
        form = ReservacionForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['proposito'],
            ['El propósito debe tener entre 10 y 200 caracteres.']
        )

    def test_asistentes_cero_invalido(self):
        self.data['asistentes'] = 0
        form = ReservacionForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['asistentes'],
            ['Asegúrese de que este valor sea mayor o igual a 1.']
        )

    def test_asistentes_negativo_invalido(self):
        self.data['asistentes'] = -2
        form = ReservacionForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['asistentes'],
            ['Asegúrese de que este valor sea mayor o igual a 1.']
        )

    def test_asistentes_texto_invalido(self):
        self.data['asistentes'] = 'cinco'
        form = ReservacionForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['asistentes'],
            ['Introduzca un número entero.']
        )

    def test_asistentes_supera_capacidad_sala_invalido(self):
        self.data['asistentes'] = 5
        form = ReservacionForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['asistentes'],
            ['El número de asistentes supera la capacidad de la sala.']
        )

    def test_fecha_pasada_invalida(self):
        self.data['fecha'] = date.today() - timedelta(days=1)
        form = ReservacionForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['fecha'],
            ['La fecha no puede ser anterior al día actual.']
        )

    def test_hora_fin_igual_a_hora_inicio_invalida(self):
        self.data['hora_inicio'] = time(10, 0)
        self.data['hora_fin'] = time(10, 0)
        form = ReservacionForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['hora_fin'],
            ['La hora de fin debe ser posterior a la hora de inicio.']
        )

    def test_hora_fin_menor_a_hora_inicio_invalida(self):
        self.data['hora_inicio'] = time(11, 0)
        self.data['hora_fin'] = time(10, 0)
        form = ReservacionForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['hora_fin'],
            ['La hora de fin debe ser posterior a la hora de inicio.']
        )

    def test_hora_inicio_antes_de_08_invalida(self):
        self.data['hora_inicio'] = time(7, 59)
        self.data['hora_fin'] = time(9, 0)
        form = ReservacionForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['hora_inicio'],
            ['La hora de inicio debe encontrarse entre 08:00 y 19:00.']
        )

    def test_hora_inicio_despues_de_19_invalida(self):
        self.data['hora_inicio'] = time(19, 1)
        self.data['hora_fin'] = time(20, 0)
        form = ReservacionForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['hora_inicio'],
            ['La hora de inicio debe encontrarse entre 08:00 y 19:00.']
        )

    def test_hora_fin_despues_de_20_invalida(self):
        self.data['hora_inicio'] = time(19, 0)
        self.data['hora_fin'] = time(20, 1)
        form = ReservacionForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['hora_fin'],
            ['La hora de fin no puede exceder las 20:00.']
        )

    def test_sala_inactiva_invalida(self):
        sala_inactiva = Sala.objects.create(
            nombre='Sala Inactiva',
            capacidad=6,
            ubicacion='Biblioteca, planta alta',
            activa=False
        )
        self.data['sala'] = sala_inactiva.id
        form = ReservacionForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['sala'],
            ['La sala no se encuentra disponible para reservación.']
        )

    def test_horario_bordes_exactos_08_y_19_a_20_valido(self):
        self.data['hora_inicio'] = time(8, 0)
        self.data['hora_fin'] = time(9, 0)
        form = ReservacionForm(data=self.data)
        self.assertTrue(form.is_valid())

        self.data['hora_inicio'] = time(19, 0)
        self.data['hora_fin'] = time(20, 0)
        form_tarde = ReservacionForm(data=self.data)
        self.assertTrue(form_tarde.is_valid())

    def test_asistentes_igual_a_capacidad_y_fecha_futura_validos(self):
        self.data['asistentes'] = 4
        self.data['fecha'] = date.today() + timedelta(days=1)
        form = ReservacionForm(data=self.data)
        self.assertTrue(form.is_valid())

