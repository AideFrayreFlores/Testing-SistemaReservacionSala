from datetime import date, datetime, time, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from salas.models import Sala
from reservaciones.models import Reservacion
from reservaciones.services import cancelar_reservacion, registrar_reservacion


class TestServicioReservacion(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='usuario1',
            password='usuario123_'
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
            registrar_reservacion(self.datos)
        self.assertEqual(
            error.exception.messages,
            [
                'La duración de la reservación debe ser de '
                'entre 30 minutos y 2 horas.'
            ]
        )

    def test_duracion_mayor_a_2_horas_invalida(self):
        self.datos['hora_inicio'] = time(10, 0)
        self.datos['hora_fin'] = time(12, 1)
        with self.assertRaises(ValidationError) as error:
            registrar_reservacion(self.datos)
        self.assertEqual(
            error.exception.messages,
            [
                'La duración de la reservación debe ser de '
                'entre 30 minutos y 2 horas.'
            ]
        )

    def test_duracion_borde_30_minutos_valida(self):
        self.datos['hora_inicio'] = time(10, 0)
        self.datos['hora_fin'] = time(10, 30)
        res_min = registrar_reservacion(self.datos)
        self.assertEqual(res_min.estado, 'VIGENTE')

    def test_duracion_borde_2_horas_valida(self):
        self.datos['hora_inicio'] = time(12, 0)
        self.datos['hora_fin'] = time(14, 0)
        res_max = registrar_reservacion(self.datos)
        self.assertEqual(res_max.estado, 'VIGENTE')

    def test_traslape_parcial_invalido(self):
        registrar_reservacion(self.datos)
        self.datos['hora_inicio'] = time(10, 30)
        self.datos['hora_fin'] = time(11, 30)
        with self.assertRaises(ValidationError) as error:
            registrar_reservacion(self.datos)
        self.assertEqual(
            error.exception.messages,
            ['La sala no está disponible en el horario solicitado.']
        )

    def test_traslape_contenido_invalido(self):
        registrar_reservacion(self.datos)
        self.datos['hora_inicio'] = time(10, 15)
        self.datos['hora_fin'] = time(10, 45)
        with self.assertRaises(ValidationError) as error:
            registrar_reservacion(self.datos)
        self.assertEqual(
            error.exception.messages,
            ['La sala no está disponible en el horario solicitado.']
        )

    def test_traslape_total_invalido(self):
        registrar_reservacion(self.datos)
        with self.assertRaises(ValidationError) as error:
            registrar_reservacion(self.datos)
        self.assertEqual(
            error.exception.messages,
            ['La sala no está disponible en el horario solicitado.']
        )

    def test_horarios_adyacentes_permitidos(self):
        registrar_reservacion(self.datos)
        self.datos['hora_inicio'] = time(11, 0)
        self.datos['hora_fin'] = time(12, 0)
        registrar_reservacion(self.datos)
        self.assertEqual(
            Reservacion.objects.filter(estado='VIGENTE').count(),
            2
        )

    def test_ignorar_reservaciones_canceladas_al_calcular_disponibilidad(self):
        res_cancelada = registrar_reservacion(self.datos)
        res_cancelada.estado = 'CANCELADA'
        res_cancelada.save()
        nueva_res = registrar_reservacion(self.datos)
        self.assertEqual(nueva_res.estado, 'VIGENTE')


class TestServicioCancelacion(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='usuario1',
            password='usuario123_'
        )
        self.otro_usuario = User.objects.create_user(
            username='usuario2',
            password='usuario567_'
        )
        self.sala = Sala.objects.create(
            nombre='Sala D',
            capacidad=4,
            ubicacion='Biblioteca, planta baja',
            activa=True
        )
        self.ahora = timezone.make_aware(
            datetime(2026, 11, 17, 10, 0)
        )
        self.reservacion = Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala,
            fecha=self.ahora.date(),
            hora_inicio=time(12, 0),
            hora_fin=time(13, 0),
            asistentes=3,
            proposito='Estudio grupal para examen'
        )

    def test_cancelar_reservacion_propia_vigente_con_anticipacion_valida(
        self
    ):
        cancelada = cancelar_reservacion(
            self.reservacion.id,
            self.usuario,
            ahora=self.ahora
        )
        self.assertEqual(cancelada.estado, 'CANCELADA')

    def test_cancelar_reservacion_propia_registra_fecha_cancelacion(self):
        cancelada = cancelar_reservacion(
            self.reservacion.id,
            self.usuario,
            ahora=self.ahora
        )
        self.assertEqual(cancelada.fecha_cancelacion, self.ahora)

    def test_rechazar_cancelacion_de_reservacion_ajena(self):
        with self.assertRaisesMessage(
            ValidationError,
            'No tienes permiso para cancelar esta reservación.'
        ):
            cancelar_reservacion(
                self.reservacion.id,
                self.otro_usuario,
                ahora=self.ahora
            )

    def test_cancelacion_ajena_conserva_reservacion_vigente(self):
        try:
            cancelar_reservacion(
                self.reservacion.id,
                self.otro_usuario,
                ahora=self.ahora
            )
        except ValidationError:
            pass
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, 'VIGENTE')

    def test_rechazar_cancelacion_con_60_minutos_exactos(self):
        self.reservacion.hora_inicio = time(11, 0)
        self.reservacion.save(update_fields=['hora_inicio'])
        with self.assertRaisesMessage(
            ValidationError,
            'El periodo de cancelación ha concluido.'
        ):
            cancelar_reservacion(
                self.reservacion.id,
                self.usuario,
                ahora=self.ahora
            )

    def test_cancelacion_con_60_minutos_conserva_estado_vigente(self):
        self.reservacion.hora_inicio = time(11, 0)
        self.reservacion.save(update_fields=['hora_inicio'])
        try:
            cancelar_reservacion(
                self.reservacion.id,
                self.usuario,
                ahora=self.ahora
            )
        except ValidationError:
            pass
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, 'VIGENTE')

    def test_rechazar_cancelacion_con_menos_de_60_minutos(self):
        self.reservacion.hora_inicio = time(10, 30)
        self.reservacion.hora_fin = time(11, 30)
        self.reservacion.save(update_fields=['hora_inicio', 'hora_fin'])
        with self.assertRaisesMessage(
            ValidationError,
            'El periodo de cancelación ha concluido.'
        ):
            cancelar_reservacion(
                self.reservacion.id,
                self.usuario,
                ahora=self.ahora
            )

    def test_cancelacion_con_menos_de_60_minutos_conserva_estado(self):
        self.reservacion.hora_inicio = time(10, 30)
        self.reservacion.hora_fin = time(11, 30)
        self.reservacion.save(update_fields=['hora_inicio', 'hora_fin'])
        try:
            cancelar_reservacion(
                self.reservacion.id,
                self.usuario,
                ahora=self.ahora
            )
        except ValidationError:
            pass
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, 'VIGENTE')

    def test_rechazar_segunda_cancelacion(self):
        cancelar_reservacion(
            self.reservacion.id, self.usuario, ahora=self.ahora
        )
        with self.assertRaisesMessage(
            ValidationError, 'La reservación ya fue cancelada.'
        ):
            cancelar_reservacion(
                self.reservacion.id,
                self.usuario,
                ahora=self.ahora + timedelta(minutes=5)
            )

    def test_segunda_cancelacion_no_cambia_fecha_original(self):
        cancelar_reservacion(
            self.reservacion.id, self.usuario, ahora=self.ahora
        )
        try:
            cancelar_reservacion(
                self.reservacion.id,
                self.usuario,
                ahora=self.ahora + timedelta(minutes=5)
            )
        except ValidationError:
            pass
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.fecha_cancelacion, self.ahora)
