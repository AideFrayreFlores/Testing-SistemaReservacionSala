from datetime import date, time
from threading import Thread
import time as time_module
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connections
from django.test import TransactionTestCase
from salas.models import Sala
from reservaciones.models import Reservacion
from reservaciones.services import registrar_reservacion


class TestConcurrenciaReservacion(TransactionTestCase):

    def setUp(self):
        self.usuario1 = User.objects.create_user(
            username='usuario1',
            password='Password123!'
        )
        self.usuario2 = User.objects.create_user(
            username='usuario2',
            password='Password123!'
        )
        self.sala = Sala.objects.create(
            nombre='Sala D',
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )
        self.datos = {
            'usuario': self.usuario1,
            'sala': self.sala,
            'fecha': date.today(),
            'hora_inicio': time(10, 0),
            'hora_fin': time(11, 0),
            'asistentes': 3,
            'proposito': 'Estudio grupal para examen'
        }
        self.errores = []

    def intentar_reservar(self, usuario):
        datos_hilo = dict(self.datos)
        datos_hilo['usuario'] = usuario
        try:
            registrar_reservacion(datos_hilo)
        except ValidationError as error:
            self.errores.append(error.messages[0])
        finally:
            connections.close_all()

    def test_solicitudes_simultaneas_solo_una_queda_vigente(self):
        create_original = Reservacion.objects.create

        def create_con_pausa(**kwargs):
            time_module.sleep(0.2)
            return create_original(**kwargs)

        with patch.object(
            Reservacion.objects,
            'create',
            side_effect=create_con_pausa
        ):
            hilo1 = Thread(
                target=self.intentar_reservar,
                args=(self.usuario1,)
            )
            hilo2 = Thread(
                target=self.intentar_reservar,
                args=(self.usuario2,)
            )
            hilo1.start()
            hilo2.start()
            hilo1.join()
            hilo2.join()

        vigentes = Reservacion.objects.filter(
            sala=self.sala,
            fecha=date.today(),
            estado='VIGENTE'
        )
        self.assertEqual(vigentes.count(), 1)
        self.assertEqual(
            self.errores,
            ['La sala no está disponible en el horario solicitado.']
        )
