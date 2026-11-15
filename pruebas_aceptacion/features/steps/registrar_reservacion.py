import os
import threading
from time import sleep
from behave import given, when, then
from behave.api.pending_step import StepNotImplementedError
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


def _crear_driver():
    opciones = webdriver.ChromeOptions()
    prefs = {
        'credentials_enable_service': False,
        'profile.password_manager_enabled': False,
        'profile.password_manager_leak_detection': False,
    }
    opciones.add_experimental_option('prefs', prefs)
    if os.getenv('HEADLESS', '0') == '1':
        opciones.add_argument('--headless=new')
    driver = webdriver.Chrome(options=opciones)
    driver.implicitly_wait(5)
    return driver


def _iniciar_sesion(username, password):
    driver = _crear_driver()
    driver.get('http://localhost:8000/usuarios/login')
    sleep(1)
    driver.find_element(By.NAME, 'username').send_keys(username)
    driver.find_element(By.NAME, 'password').send_keys(password)
    sleep(1)
    driver.find_element(By.ID, 'btn-login').click()
    sleep(5)
    return driver


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


def _cerrar_drivers(drivers):
    for driver in drivers:
        driver.quit()


@given(u'que ingreso al sistema de reservaciones')
def step_impl(context):
    context.driver = _crear_driver()
    context.driver.get('http://localhost:8000/usuarios/login')
    sleep(1)


@given(u'escribo el usuario "{username}" y la contraseña "{password}"')
def step_impl(context, username, password):
    context.driver.find_element(By.NAME, 'username').send_keys(username)
    context.driver.find_element(By.NAME, 'password').send_keys(password)
    sleep(1)


@given(u'presiono el botón Ingresar')
def step_impl(context):
    context.driver.find_element(By.ID, 'btn-login').click()
    sleep(5)


@given(u'doy click en el botón Nueva reservación')
def step_impl(context):
    context.driver.find_element(By.ID, 'btn-nueva-reservacion').click()
    sleep(2)


@given(u'selecciono la sala "{nombre_sala}"')
def step_impl(context, nombre_sala):
    selecion_sala = Select(context.driver.find_element(By.ID, 'id_sala'))
    selecion_sala.select_by_visible_text(nombre_sala)
    sleep(1)


@given(
    u'capturo la fecha "{fecha}", hora de inicio "{inicio}" '
    u'y hora de fin "{fin}"'
)
def step_impl(context, fecha, inicio, fin):
    _capturar_fecha_y_horas(context.driver, fecha, inicio, fin)
    sleep(1)


@given(
    u'capturo el número de asistentes "{asistentes}" '
    u'y el propósito "{proposito}"'
)
def step_impl(context, asistentes, proposito):
    context.driver.find_element(By.ID, 'id_asistentes').send_keys(asistentes)
    context.driver.find_element(By.ID, 'id_proposito').send_keys(proposito)
    sleep(2)


@when(u'presiono el botón Guardar reservación')
def step_impl(context):
    context.driver.find_element(By.ID, 'btn-guardar-reservacion').click()
    sleep(2)


@then(u'puedo ver el mensaje de confirmación "{mensaje}"')
def step_impl(context, mensaje):
    obtenido = context.driver.find_element(By.ID, 'mensaje-confirmacion').text
    context.driver.quit()
    assert mensaje in obtenido, (
        f'Mensaje esperado es {mensaje} y el obtenido es {obtenido}'
    )


@then(u'puedo ver el mensaje de error "{mensaje}"')
def step_impl(context, mensaje):
    obtenido = context.driver.find_element(By.ID, 'error-servicio').text
    context.driver.quit()
    assert mensaje in obtenido, (
        f'Mensaje esperado es {mensaje} y el obtenido es {obtenido}'
    )


@then(u'puedo ver el mensaje de error en el formulario "{mensaje}"')
def step_impl(context, mensaje):
    obtenido = context.driver.find_element(By.CLASS_NAME, 'errorlist').text
    context.driver.quit()
    assert mensaje in obtenido, (
        f'Mensaje esperado es {mensaje} y el obtenido es {obtenido}'
    )


@then(u'puedo ver el mensaje de error de validación "{mensaje}"')
def step_impl(context, mensaje):
    obtenido = context.driver.find_element(By.CLASS_NAME, 'errorlist').text
    context.driver.quit()
    assert mensaje in obtenido, (
        f'Mensaje esperado es {mensaje} y el obtenido es {obtenido}'
    )


@then(
    u'puedo ver los mensajes de error de fecha "{error_fecha}" '
    u'y de horario "{error_horario}"'
)
def step_impl(context, error_fecha, error_horario):
    obtenido = context.driver.find_element(By.ID, 'reservacion-form').text
    context.driver.quit()
    assert error_fecha in obtenido and error_horario in obtenido, (
        f'Mensajes esperados {error_fecha} y {error_horario}, '
        f'obtenido: {obtenido}'
    )


@then(u'puedo ver el mensaje de error de sala inactiva "{mensaje}"')
def step_impl(context, mensaje):
    obtenido = context.driver.find_element(By.CLASS_NAME, 'errorlist').text
    context.driver.quit()
    assert mensaje in obtenido, (
        f'Mensaje esperado es {mensaje} y el obtenido es {obtenido}'
    )


@given(
    u'que dos usuarios "{user1}" con contraseña "{pass1}" '
    u'y "{user2}" con contraseña "{pass2}" ingresan al sistema '
    u'de reservaciones'
)
def step_impl(context, user1, pass1, user2, pass2):
    context.drivers = [
        _iniciar_sesion(user1, pass1),
        _iniciar_sesion(user2, pass2),
    ]


@given(u'ambos abren el formulario de nueva reservación')
def step_impl(context):
    for driver in context.drivers:
        driver.find_element(By.ID, 'btn-nueva-reservacion').click()
    sleep(2)


@given(u'ambos seleccionan la sala "{nombre_sala}"')
def step_impl(context, nombre_sala):
    for driver in context.drivers:
        seleccion = Select(driver.find_element(By.ID, 'id_sala'))
        seleccion.select_by_visible_text(nombre_sala)
    sleep(1)


@given(
    u'ambos capturan la fecha "{fecha}", hora de inicio "{inicio}" '
    u'y hora de fin "{fin}"'
)
def step_impl(context, fecha, inicio, fin):
    for driver in context.drivers:
        _capturar_fecha_y_horas(driver, fecha, inicio, fin)
    sleep(1)


@given(
    u'ambos capturan el número de asistentes "{asistentes}" '
    u'y el propósito "{proposito}"'
)
def step_impl(context, asistentes, proposito):
    for driver in context.drivers:
        driver.find_element(By.ID, 'id_asistentes').send_keys(asistentes)
        driver.find_element(By.ID, 'id_proposito').send_keys(proposito)
    sleep(1)


@when(u'ambos presionan el botón Guardar reservación al mismo tiempo')
def step_impl(context):
    barrera = threading.Barrier(2)

    def enviar(driver):
        boton = driver.find_element(By.ID, 'btn-guardar-reservacion')
        barrera.wait(timeout=5)
        boton.click()

    hilos = [
        threading.Thread(target=enviar, args=(driver,))
        for driver in context.drivers
    ]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()
    sleep(3)


@then(u'solo una solicitud ve el mensaje de confirmación "{mensaje}"')
def step_impl(context, mensaje):
    confirmaciones = []
    for driver in context.drivers:
        elementos = driver.find_elements(By.ID, 'mensaje-confirmacion')
        if elementos and mensaje in elementos[0].text:
            confirmaciones.append(elementos[0].text)
    if len(confirmaciones) != 1:
        _cerrar_drivers(context.drivers)
    assert len(confirmaciones) == 1, (
        f'Se esperaba 1 confirmación con "{mensaje}", '
        f'se obtuvieron {len(confirmaciones)}'
    )


@then(u'la otra solicitud ve el mensaje de error "{mensaje}"')
def step_impl(context, mensaje):
    errores = []
    try:
        for driver in context.drivers:
            elementos = driver.find_elements(By.ID, 'error-servicio')
            if elementos and mensaje in elementos[0].text:
                errores.append(elementos[0].text)
    finally:
        _cerrar_drivers(context.drivers)
    assert len(errores) == 1, (
        f'Se esperaba 1 error con "{mensaje}", '
        f'se obtuvieron {len(errores)}'
    )


@then(u'puedo ver el mensaje "{mensaje}" en los campos "{campos}"')
def step_impl(context, mensaje, campos):
    context.driver.quit()
    raise StepNotImplementedError(
        u'Then puedo ver el mensaje "{mensaje}" en los campos "{campos}"'
    )
