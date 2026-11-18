"""Pasos de aceptación para CA-07, CA-08 y CA-09 de la cancelación.

El horario de prueba de CA-07 y CA-08 se elige al azar entre 30 y 180 días
futuros, en bloques de 30 minutos dentro del horario institucional. Así, las
ejecuciones repetidas no reutilizan el mismo espacio con alta probabilidad.
Las reservaciones de prueba se identifican por sus propósitos ("... CA-07",
"CA-08 ..."), lo que permitirá una limpieza determinista en un commit
posterior; este archivo no ejecuta comandos de limpieza.

CA-08 crea la reservación por la interfaz como su propietario, recuerda la
acción de cancelar de su fila y comprueba, desde una sesión distinta, que ni
la fila ni la acción se muestran y que un POST con el token CSRF de la sesión
intrusa recibe el rechazo controlado del servidor sin revelar el propósito.

CA-09 usa el fixture `preparar_reserva_ca09`, que crea una sola reservación
de alumno1 a 30 minutos del momento actual; así el periodo de cancelación ya
concluyó sin congelar el reloj. El escenario comprueba el aviso, la ausencia
del botón, el rechazo controlado del POST y el estado VIGENTE. `environment.py`
elimina esa fila por identificador al terminar el escenario.

CA-10 es una regresión de negocio: crea su propia reservación por la interfaz,
recuerda la acción de cancelar, la cancela con el botón real y guarda la fecha
de cancelación mostrada; después reenvía el POST a la acción recordada. El
servidor rechaza la segunda cancelación y el escenario comprueba que el badge
CANCELADA y la fecha original no cambian.

El cambio de usuario reutiliza los pasos de autenticación de Aide. Behave
asocia cada paso a su tipo por la palabra clave, así que el cierre de sesión
y los ingresos posteriores del escenario se declaran como "Dado" en el
feature. El POST de prueba y la verificación del mensaje de rechazo quedan
genéricos para reutilizarlos en CA-09 y CA-10.
"""

import os
import random
import re
from datetime import date, datetime, time, timedelta
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from behave import given, then, when
from fixture_ca09 import preparar as preparar_reserva_ca09
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
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
GUION_FORMULARIO_POST = """
var token = document.querySelector(
    'input[name="csrfmiddlewaretoken"]'
).value;
var formulario = document.createElement('form');
formulario.method = 'post';
formulario.action = arguments[0];
var campo = document.createElement('input');
campo.type = 'hidden';
campo.name = 'csrfmiddlewaretoken';
campo.value = token;
formulario.appendChild(campo);
var boton = document.createElement('button');
boton.type = 'submit';
boton.id = 'btn-post-ca08';
boton.textContent = 'Enviar petición de prueba';
formulario.appendChild(boton);
document.body.appendChild(formulario);
"""


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
        try:
            errores = driver.find_elements(By.ID, 'error-servicio')
            if errores and errores[0].text.strip():
                raise AssertionError(
                    'No se registró la reservación: '
                    f'{errores[0].text.strip()}'
                )
            errores_formulario = driver.find_elements(
                By.CLASS_NAME, 'errorlist'
            )
            if errores_formulario and errores_formulario[0].text.strip():
                raise AssertionError(
                    'No se registró la reservación: '
                    f'{errores_formulario[0].text.strip()}'
                )
            mensajes = driver.find_elements(By.ID, 'mensaje-confirmacion')
            return bool(
                mensajes and MENSAJE_REGISTRO in mensajes[0].text
            )
        except StaleElementReferenceException:
            # Igual que en la cancelación, el siguiente sondeo reubica los
            # elementos cuando la navegación reemplaza el DOM.
            return False

    _esperar(
        context,
        resultado,
        'no apareció la confirmación del registro de la reservación'
    )


def _esperar_cancelacion(context):
    def resultado(driver):
        try:
            mensajes = driver.find_elements(By.ID, 'mensaje-confirmacion')
            if not mensajes:
                return False
            texto = mensajes[0].text.strip()
        except StaleElementReferenceException:
            # La redirección reemplazó el DOM entre el hallazgo y la lectura;
            # el siguiente sondeo vuelve a localizar los elementos.
            return False
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


def _fila_por_proposito(context, proposito, estado,
                        fecha=None, horario=None):
    """Localiza la fila del propósito dentro del horario preparado.

    El filtro por fecha, horario y estado evita confundirla con filas de
    ejecuciones anteriores que usaron el mismo propósito. CA-09 pasa la
    fecha y el horario devueltos por su fixture en lugar de los de CA-07.
    """

    fecha = fecha or context.fecha_ca07
    horario = horario or _horario_esperado(context)

    def localizar(driver):
        filas = driver.find_elements(
            By.CSS_SELECTOR, '#tabla-reservaciones tbody tr'
        )
        for fila in filas:
            celdas = fila.find_elements(By.TAG_NAME, 'td')
            if len(celdas) < 8 or celdas[4].text.strip() != proposito:
                continue
            if not _fecha_coincide(celdas[1].text, fecha):
                continue
            if ' '.join(celdas[2].text.split()) != horario:
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


def _fila_ca09(context, proposito, estado):
    return _fila_por_proposito(
        context,
        proposito,
        estado,
        fecha=context.fecha_ca09,
        horario=context.horario_ca09
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


def _accion_de_cancelar(fila):
    formulario = fila.find_element(By.CSS_SELECTOR, 'form[action]')
    return urlparse(formulario.get_attribute('action')).path


def _fecha_de_cancelacion(fila):
    celda = fila.find_element(
        By.CSS_SELECTOR, 'td.fecha-cancelacion'
    ).text.strip()
    assert PATRON_FECHA_CANCELACION.fullmatch(celda), (
        'La celda de cancelación no muestra fecha y hora: '
        f'"{celda}"'
    )
    return celda


def _identidad_de_fila(fila):
    celdas = fila.find_elements(By.TAG_NAME, 'td')
    return (celdas[1].text.strip(), ' '.join(celdas[2].text.split()))


def _recordar_accion(context, proposito):
    fila = _fila_por_proposito(context, proposito, 'VIGENTE')
    context.accion_cancelacion = _accion_de_cancelar(fila)
    context.identidad_fila = _identidad_de_fila(fila)


def _esperar_rechazo(context, mensaje):
    def resultado(driver):
        try:
            alertas = driver.find_elements(By.ID, 'mensaje-confirmacion')
            return next(
                (alerta for alerta in alertas if mensaje in alerta.text),
                False
            )
        except StaleElementReferenceException:
            return False

    return _esperar(
        context,
        resultado,
        f'no apareció el mensaje de rechazo "{mensaje}"'
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
    celda_cancelacion = _fecha_de_cancelacion(fila)
    assert celda_cancelacion.startswith(
        _fecha_local().strftime('%d/%m/%Y')
    ), (
        'La fecha de cancelación no corresponde al día actual: '
        f'"{celda_cancelacion}"'
    )
    _verificar_fecha_y_horario(context, fila)


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


@given(u'que preparo una reservación que inicia en 30 minutos')
def step_impl(context):
    datos = preparar_reserva_ca09()
    context.reserva_ca09_id = datos['id']
    context.fecha_ca09 = date.fromisoformat(datos['fecha'])
    context.horario_ca09 = (
        f'{datos["hora_inicio"]} - {datos["hora_fin"]}'
    )
    context.accion_cancelacion = (
        f'/reservaciones/cancelar/{datos["id"]}'
    )


@given(
    u'recuerdo la acción de cancelar de la reservación "{proposito}"'
)
def step_impl(context, proposito):
    _recordar_accion(context, proposito)


@given(u'que cierro sesión')
def step_impl(context):
    boton = _esperar(
        context,
        EC.element_to_be_clickable((By.ID, 'btn-logout')),
        'no apareció el botón Cerrar sesión'
    )
    boton.click()
    _esperar(
        context,
        EC.presence_of_element_located((By.ID, 'btn-login')),
        'no se mostró el formulario de ingreso después de cerrar sesión'
    )


@then(u'la reservación "{proposito}" no aparece en mi lista')
def step_impl(context, proposito):
    _esperar(
        context,
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, '.card-header h2')
        ),
        'no se mostró la lista de reservaciones del usuario'
    )
    assert proposito not in context.driver.page_source, (
        f'La reservación ajena "{proposito}" es visible para otro usuario.'
    )


@then(u'no veo la acción de cancelar de la reservación recordada')
def step_impl(context):
    assert context.accion_cancelacion not in context.driver.page_source, (
        'La acción de cancelar de la reservación ajena sigue visible: '
        f'{context.accion_cancelacion}'
    )


@when(u'envío una petición POST de cancelación a la acción recordada')
def step_impl(context):
    context.driver.execute_script(
        GUION_FORMULARIO_POST, context.accion_cancelacion
    )
    boton = _esperar(
        context,
        EC.element_to_be_clickable((By.ID, 'btn-post-ca08')),
        'no se preparó la petición POST de prueba'
    )
    boton.click()


@then(u'puedo ver el mensaje de rechazo "{mensaje}"')
def step_impl(context, mensaje):
    alerta = _esperar_rechazo(context, mensaje)
    assert 'alert-error' in alerta.get_attribute('class'), (
        'El mensaje de rechazo no se presentó como error controlado.'
    )
    assert context.driver.current_url.rstrip('/').endswith('/reservaciones'), (
        'El rechazo no regresó a la lista de reservaciones: '
        f'{context.driver.current_url}'
    )


@then(u'el rechazo no revela el propósito "{proposito}"')
def step_impl(context, proposito):
    assert proposito not in context.driver.page_source, (
        'El rechazo divulgó el propósito de la reservación ajena.'
    )


@then(u'guardo una captura llamada "{nombre}"')
def step_impl(context, nombre):
    _guardar_evidencia(context, nombre)


@then(
    u'la reservación "{proposito}" sigue vigente con su acción de cancelar'
)
def step_impl(context, proposito):
    fila = _fila_por_proposito(context, proposito, 'VIGENTE')
    badge = fila.find_element(By.CSS_SELECTOR, 'span.badge-vigente').text
    assert badge.strip() == 'VIGENTE', (
        f'Estado esperado VIGENTE y obtenido {badge}'
    )
    assert _accion_de_cancelar(fila) == context.accion_cancelacion, (
        'La acción de cancelar de la reservación cambió tras el intento ajeno.'
    )
    assert _identidad_de_fila(fila) == context.identidad_fila, (
        'La fecha u horario de la reservación cambiaron tras el intento ajeno.'
    )


@then(u'la reservación "{proposito}" no muestra la acción de cancelar')
def step_impl(context, proposito):
    fila = _fila_ca09(context, proposito, 'VIGENTE')
    assert not fila.find_elements(By.CSS_SELECTOR, 'form[action]'), (
        'La reservación fuera del periodo muestra el formulario de cancelar.'
    )
    assert not fila.find_elements(By.CSS_SELECTOR, 'button.btn-cancelar'), (
        'La reservación fuera del periodo muestra el botón de cancelar.'
    )


@then(u'la reservación "{proposito}" muestra el aviso "{aviso}"')
def step_impl(context, proposito, aviso):
    fila = _fila_ca09(context, proposito, 'VIGENTE')
    elemento = fila.find_element(
        By.CSS_SELECTOR, 'span.aviso-cancelacion'
    )
    obtenido = elemento.text.strip()
    assert obtenido == aviso, (
        f'Aviso esperado "{aviso}" y obtenido "{obtenido}"'
    )


@then(
    u'la reservación "{proposito}" sigue vigente sin acción de cancelar'
)
def step_impl(context, proposito):
    fila = _fila_ca09(context, proposito, 'VIGENTE')
    badge = fila.find_element(By.CSS_SELECTOR, 'span.badge-vigente').text
    assert badge.strip() == 'VIGENTE', (
        f'Estado esperado VIGENTE y obtenido {badge}'
    )
    assert not fila.find_elements(By.CSS_SELECTOR, 'form[action]'), (
        'El rechazo dejó visible la acción de cancelar de la reservación.'
    )


@then(
    u'la reservación "{proposito}" queda cancelada sin acción de cancelar'
)
def step_impl(context, proposito):
    fila = _fila_por_proposito(context, proposito, 'CANCELADA')
    badge = fila.find_element(By.CSS_SELECTOR, 'span.badge-cancelada').text
    assert badge.strip() == 'CANCELADA', (
        f'Estado esperado CANCELADA y obtenido {badge}'
    )
    assert not fila.find_elements(By.CSS_SELECTOR, 'form[action]'), (
        'La reservación cancelada conserva el formulario de cancelar.'
    )
    assert not fila.find_elements(By.CSS_SELECTOR, 'button.btn-cancelar'), (
        'La reservación cancelada conserva el botón de cancelar.'
    )
    context.fecha_cancelacion_ca10 = _fecha_de_cancelacion(fila)


@then(
    u'la reservación "{proposito}" sigue cancelada con la misma '
    u'fecha de cancelación'
)
def step_impl(context, proposito):
    fila = _fila_por_proposito(context, proposito, 'CANCELADA')
    badge = fila.find_element(By.CSS_SELECTOR, 'span.badge-cancelada').text
    assert badge.strip() == 'CANCELADA', (
        f'Estado esperado CANCELADA y obtenido {badge}'
    )
    assert not fila.find_elements(By.CSS_SELECTOR, 'form[action]'), (
        'El rechazo restauró la acción de cancelar de la reservación.'
    )
    fecha = _fecha_de_cancelacion(fila)
    assert fecha == context.fecha_cancelacion_ca10, (
        'La fecha de cancelación cambió tras el segundo intento: esperada '
        f'"{context.fecha_cancelacion_ca10}" y obtenida "{fecha}"'
    )
