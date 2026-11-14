from datetime import date, time
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from salas.models import Sala
from reservaciones.services import registrar_reservacion


class TestServicioReservacion(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='usuario1',
            password='Password123!'
        )
        self.sala = Sala.objects.create(
            nombre='Sala D',
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )
        self.datos = {
            'usuario': self.usuario,
            'sala': self.sala,
            'fecha': date.today(),
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0),
            'asistentes': 3,
            'proposito': 'Estudio grupal para examen'
        }

    def test_duracion_menor_a_30_minutos_invalida(self):
        self.datos['hora_inicio'] = time(10, 0)
        self.datos['hora_fin'] = time(10, 29)
        with self.assertRaises(ValidationError) as error:
            registrar_reservacion(**self.datos)
        self.assertEqual(
            error.exception.messages,
            ['La duración de la reservación debe ser de entre 30 minutos y 2 horas.']
        )

    def test_duracion_mayor_a_2_horas_invalida(self):
        self.datos['hora_inicio'] = time(10, 0)
        self.datos['hora_fin'] = time(12, 1)
        with self.assertRaises(ValidationError) as error:
            registrar_reservacion(**self.datos)
        self.assertEqual(
            error.exception.messages,
            ['La duración de la reservación debe ser de entre 30 minutos y 2 horas.']
        )

    def test_duracion_bordes_30_min_y_2_horas_valida(self):
        self.datos['hora_inicio'] = time(10, 0)
        self.datos['hora_fin'] = time(10, 30)
        res_min = registrar_reservacion(**self.datos)
        self.assertEqual(res_min.estado, 'VIGENTE')

        self.datos['hora_inicio'] = time(12, 0)
        self.datos['hora_fin'] = time(14, 0)
        res_max = registrar_reservacion(**self.datos)
        self.assertEqual(res_max.estado, 'VIGENTE')

    def test_traslape_parcial_invalido(self):
        registrar_reservacion(**self.datos)
        self.datos['hora_inicio'] = time(10, 30)
        self.datos['hora_fin'] = time(11, 30)
        with self.assertRaises(ValidationError) as error:
            registrar_reservacion(**self.datos)
        self.assertEqual(
            error.exception.messages,
            ['La sala no está disponible en el horario solicitado.']
        )

    def test_traslape_contenido_invalido(self):
        registrar_reservacion(**self.datos)
        self.datos['hora_inicio'] = time(10, 15)
        self.datos['hora_fin'] = time(10, 45)
        with self.assertRaises(ValidationError) as error:
            registrar_reservacion(**self.datos)
        self.assertEqual(
            error.exception.messages,
            ['La sala no está disponible en el horario solicitado.']
        )

    def test_traslape_total_invalido(self):
        registrar_reservacion(**self.datos)
        with self.assertRaises(ValidationError) as error:
            registrar_reservacion(**self.datos)
        self.assertEqual(
            error.exception.messages,
            ['La sala no está disponible en el horario solicitado.']
        )

    def test_horarios_adyacentes_permitidos(self):
        res1 = registrar_reservacion(**self.datos)
        self.datos['hora_inicio'] = time(11, 0)
        self.datos['hora_fin'] = time(12, 0)
        res2 = registrar_reservacion(**self.datos)
        self.assertEqual(res1.estado, 'VIGENTE')
        self.assertEqual(res2.estado, 'VIGENTE')

    def test_ignorar_reservaciones_canceladas_al_calcular_disponibilidad(self):
        res_cancelada = registrar_reservacion(**self.datos)
        res_cancelada.estado = 'CANCELADA'
        res_cancelada.save()
        nueva_res = registrar_reservacion(**self.datos)
        self.assertEqual(nueva_res.estado, 'VIGENTE')


