"""Pasos de aceptación para CA-07: cancelar y volver a reservar.

El horario de prueba se elige al azar entre 30 y 180 días futuros, en bloques
de 30 minutos dentro del horario institucional. Así, las ejecuciones repetidas
no reutilizan el mismo espacio con alta probabilidad. Las reservaciones de
prueba se identifican por sus propósitos ("... CA-07"), lo que permitirá una
limpieza determinista en un commit posterior; este archivo no ejecuta
comandos de limpieza.
"""

import os
import random
import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from behave import given, then, when
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

ESPERA_SEGUNDOS = 10
ZONA_HORARIA = 'America/Mexico_City'
PATRON_FECHA_CANCELACION = re.compile(r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$')
MENSAJE_REGISTRO = 'Reservación registrada exitosamente.'
MENSAJE_CANCELACION = 'Reservación cancelada exitosamente.'
MESES_ES = (
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
)


def _esperar(context, condicion, descripcion):
    try:
        return WebDriverWait(context.driver, ESPERA_SEGUNDOS).until(condicion)
    except TimeoutException as error:
        raise AssertionError(
            f'Tiempo de espera agotado: {descripcion}'
        ) from error


def _fecha_local():
    try:
        return datetime.now(ZoneInfo(ZONA_HORARIA)).date()
    except ZoneInfoNotFoundError:
        return datetime.now().date()


def _capturar_fecha_y_horas(driver, fecha, inicio, fin):
    campos = [
        ('id_fecha', fecha),
        ('id_hora_inicio', inicio),
        ('id_hora_fin', fin),
    ]
    for campo_id, valor in campos:
        campo = driver.find_element(By.ID, campo_id)
        campo.clear()
        driver.execute_script(
            "arguments[0].value = arguments[1];",
            campo,
            valor
        )


def _abrir_formulario(context):
    boton = _esperar(
        context,
        EC.element_to_be_clickable((By.ID, 'btn-nueva-reservacion')),
        'no apareció el botón Nueva reservación'
    )
    boton.click()
    _esperar(
        context,
        EC.presence_of_element_located((By.ID, 'reservacion-form')),
        'no se abrió el formulario de nueva reservación'
    )


def _esperar_registro(context):
    def resultado(driver):
        errores = driver.find_elements(By.ID, 'error-servicio')
        if errores and errores[0].text.strip():
            raise AssertionError(
                f'No se registró la reservación: {errores[0].text.strip()}'
            )
        errores_formulario = driver.find_elements(By.CLASS_NAME, 'errorlist')
        if errores_formulario and errores_formulario[0].text.strip():
            raise AssertionError(
                'No se registró la reservación: '
                f'{errores_formulario[0].text.strip()}'
            )
        mensajes = driver.find_elements(By.ID, 'mensaje-confirmacion')
        return bool(
            mensajes and MENSAJE_REGISTRO in mensajes[0].text
        )

    _esperar(
        context,
        resultado,
        'no apareció la confirmación del registro de la reservación'
    )


def _esperar_cancelacion(context):
    def resultado(driver):
        mensajes = driver.find_elements(By.ID, 'mensaje-confirmacion')
        if not mensajes:
            return False
        texto = mensajes[0].text.strip()
        if MENSAJE_CANCELACION in texto:
            return True
        if MENSAJE_REGISTRO in texto:
            return False
        raise AssertionError(
            f'La cancelación no se completó: {texto}'
        )

    _esperar(
        context,
        resultado,
        'no apareció la confirmación de la cancelación'
    )


def _llenar_y_guardar(context, proposito):
    _abrir_formulario(context)
    seleccion = Select(context.driver.find_element(By.ID, 'id_sala'))
    seleccion.select_by_visible_text(context.sala_ca07)
    _capturar_fecha_y_horas(
        context.driver,
        context.fecha_ca07.strftime('%Y-%m-%d'),
        context.hora_inicio_ca07.strftime('%H:%M'),
        context.hora_fin_ca07.strftime('%H:%M'),
    )
    context.driver.find_element(By.ID, 'id_asistentes').send_keys('2')
    context.driver.find_element(By.ID, 'id_proposito').send_keys(proposito)
    context.driver.find_element(By.ID, 'btn-guardar-reservacion').click()
    _esperar_registro(context)


def _horario_esperado(context):
    return (
        f'{context.hora_inicio_ca07.strftime("%H:%M")} - '
        f'{context.hora_fin_ca07.strftime("%H:%M")}'
    )


def _fecha_coincide(texto, fecha):
    numeros = [int(token) for token in re.findall(r'\d+', texto)]
    return (
        fecha.year in numeros
        and fecha.day in numeros
        and (
            MESES_ES[fecha.month - 1] in texto.lower()
            or fecha.month in numeros
        )
    )


def _estado_fila(fila):
    badges = fila.find_elements(
        By.CSS_SELECTOR, 'span.badge-vigente, span.badge-cancelada'
    )
    return badges[0].text.strip() if badges else ''


def _fila_por_proposito(context, proposito, estado):
    """Localiza la fila del propósito dentro del horario preparado.

    El filtro por fecha, horario y estado evita confundirla con filas de
    ejecuciones anteriores que usaron el mismo propósito.
    """

    def localizar(driver):
        filas = driver.find_elements(
            By.CSS_SELECTOR, '#tabla-reservaciones tbody tr'
        )
        for fila in filas:
            celdas = fila.find_elements(By.TAG_NAME, 'td')
            if len(celdas) < 8 or celdas[4].text.strip() != proposito:
                continue
            if not _fecha_coincide(celdas[1].text, context.fecha_ca07):
                continue
            if ' '.join(celdas[2].text.split()) != _horario_esperado(context):
                continue
            if _estado_fila(fila) != estado:
                continue
            return fila
        return False

    return _esperar(
        context,
        localizar,
        f'no se encontró la reservación "{proposito}" en estado '
        f'{estado} dentro del horario preparado'
    )


def _verificar_fecha_y_horario(context, fila):
    celdas = fila.find_elements(By.TAG_NAME, 'td')
    fecha_texto = celdas[1].text.strip()
    horario_texto = ' '.join(celdas[2].text.split())
    assert fecha_texto and fecha_texto != '—', 'La celda de fecha está vacía.'
    assert _fecha_coincide(fecha_texto, context.fecha_ca07), (
        f'La fecha mostrada no corresponde a la esperada: {fecha_texto}'
    )
    esperado = _horario_esperado(context)
    assert horario_texto == esperado, (
        f'Horario esperado "{esperado}" y obtenido "{horario_texto}"'
    )


def _guardar_evidencia(context, nombre):
    directorio = os.getenv('EVIDENCIA_HU02')
    if not directorio:
        return
    os.makedirs(directorio, exist_ok=True)
    ruta = os.path.join(directorio, nombre)
    if not context.driver.save_screenshot(ruta):
        raise AssertionError(f'No se pudo guardar la evidencia en {ruta}')


@given(u'preparo un horario futuro de prueba en "{nombre_sala}"')
def step_impl(context, nombre_sala):
    # El layout recorta la columna de acciones en viewports angostos (el modo
    # headless arranca en ~800 px); se usa un ancho de escritorio para poder
    # pulsar el botón real de cancelación.
    context.driver.set_window_size(1400, 900)
    context.sala_ca07 = nombre_sala
    context.fecha_ca07 = _fecha_local() + timedelta(
        days=random.randint(30, 180)
    )
    hora = random.randint(8, 18)
    minuto = random.choice((0, 30))
    context.hora_inicio_ca07 = time(hora, minuto)
    context.hora_fin_ca07 = (
        datetime.combine(context.fecha_ca07, context.hora_inicio_ca07)
        + timedelta(hours=1)
    ).time()


@given(
    u'registro una reservación en ese horario con propósito "{proposito}"'
)
def step_impl(context, proposito):
    _llenar_y_guardar(context, proposito)


@when(u'confirmo la cancelación de la reservación "{proposito}"')
def step_impl(context, proposito):
    fila = _fila_por_proposito(context, proposito, 'VIGENTE')
    fila.find_element(By.CSS_SELECTOR, 'button.btn-cancelar').click()
    alerta = _esperar(
        context,
        EC.alert_is_present(),
        'no apareció la confirmación del navegador para cancelar'
    )
    alerta.accept()
    _esperar_cancelacion(context)


@then(
    u'la reservación "{proposito}" aparece cancelada con fecha y hora'
)
def step_impl(context, proposito):
    fila = _fila_por_proposito(context, proposito, 'CANCELADA')
    badge = fila.find_element(By.CSS_SELECTOR, 'span.badge-cancelada').text
    assert badge.strip() == 'CANCELADA', (
        f'Estado esperado CANCELADA y obtenido {badge}'
    )
    celda_cancelacion = fila.find_element(
        By.CSS_SELECTOR, 'td.fecha-cancelacion'
    ).text.strip()
    assert PATRON_FECHA_CANCELACION.fullmatch(celda_cancelacion), (
        'La celda de cancelación no muestra fecha y hora: '
        f'"{celda_cancelacion}"'
    )
    assert celda_cancelacion.startswith(
        _fecha_local().strftime('%d/%m/%Y')
    ), (
        'La fecha de cancelación no corresponde al día actual: '
        f'"{celda_cancelacion}"'
    )
    _verificar_fecha_y_horario(context, fila)
    _guardar_evidencia(context, 'CA07_historial_cancelada.png')


@when(
    u'registro otra reservación en el mismo horario '
    u'con propósito "{proposito}"'
)
def step_impl(context, proposito):
    _llenar_y_guardar(context, proposito)


@then(u'la reservación "{proposito}" aparece vigente')
def step_impl(context, proposito):
    fila = _fila_por_proposito(context, proposito, 'VIGENTE')
    badge = fila.find_element(By.CSS_SELECTOR, 'span.badge-vigente').text
    assert badge.strip() == 'VIGENTE', (
        f'Estado esperado VIGENTE y obtenido {badge}'
    )
    _verificar_fecha_y_horario(context, fila)
    _guardar_evidencia(
        context, 'CA07_nueva_reservacion_mismo_horario.png'
    )
