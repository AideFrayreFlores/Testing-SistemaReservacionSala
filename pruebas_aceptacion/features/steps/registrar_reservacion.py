import threading
from time import sleep
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


def _iniciar_sesion(context, username, password):
    driver = context.crear_driver()
    driver.get(f'{context.base_url}/usuarios/login')
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


@given(u'que ingreso al sistema de reservaciones')
def step_impl(context):
    context.driver = context.crear_driver()
    context.driver.get(f'{context.base_url}/usuarios/login')
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
    assert mensaje in obtenido, (
        f'Mensaje esperado es {mensaje} y el obtenido es {obtenido}'
    )


@then(u'puedo ver el mensaje de error "{mensaje}"')
def step_impl(context, mensaje):
    obtenido = context.driver.find_element(By.ID, 'error-servicio').text
    assert mensaje in obtenido, (
        f'Mensaje esperado es {mensaje} y el obtenido es {obtenido}'
    )


@then(u'puedo ver el mensaje de error en el formulario "{mensaje}"')
def step_impl(context, mensaje):
    obtenido = context.driver.find_element(By.CLASS_NAME, 'errorlist').text
    assert mensaje in obtenido, (
        f'Mensaje esperado es {mensaje} y el obtenido es {obtenido}'
    )


@then(u'puedo ver el mensaje de error de validación "{mensaje}"')
def step_impl(context, mensaje):
    obtenido = context.driver.find_element(By.CLASS_NAME, 'errorlist').text
    assert mensaje in obtenido, (
        f'Mensaje esperado es {mensaje} y el obtenido es {obtenido}'
    )


@then(
    u'puedo ver los mensajes de error de fecha "{error_fecha}" '
    u'y de horario "{error_horario}"'
)
def step_impl(context, error_fecha, error_horario):
    obtenido = context.driver.find_element(By.ID, 'reservacion-form').text
    assert error_fecha in obtenido and error_horario in obtenido, (
        f'Mensajes esperados {error_fecha} y {error_horario}, '
        f'obtenido: {obtenido}'
    )


@then(u'puedo ver el mensaje de error de sala inactiva "{mensaje}"')
def step_impl(context, mensaje):
    obtenido = context.driver.find_element(By.CLASS_NAME, 'errorlist').text
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
        _iniciar_sesion(context, user1, pass1),
        _iniciar_sesion(context, user2, pass2),
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
    assert len(confirmaciones) == 1, (
        f'Se esperaba 1 confirmación con "{mensaje}", '
        f'se obtuvieron {len(confirmaciones)}'
    )


@then(u'la otra solicitud ve el mensaje de error "{mensaje}"')
def step_impl(context, mensaje):
    errores = []
    for driver in context.drivers:
        elementos = driver.find_elements(By.ID, 'error-servicio')
        if elementos and mensaje in elementos[0].text:
            errores.append(elementos[0].text)
    assert len(errores) == 1, (
        f'Se esperaba 1 error con "{mensaje}", '
        f'se obtuvieron {len(errores)}'
    )


@then(u'puedo ver el mensaje "{mensaje}" en los campos "{campos}"')
def step_impl(context, mensaje, campos):
    sala = context.driver.find_element(
        By.XPATH, '//*[@id="id_sala"]/../ul'
    ).text
    fecha = context.driver.find_element(
        By.XPATH, '//*[@id="id_fecha"]/../ul'
    ).text
    inicio = context.driver.find_element(
        By.XPATH, '//*[@id="id_hora_inicio"]/../ul'
    ).text
    fin = context.driver.find_element(
        By.XPATH, '//*[@id="id_hora_fin"]/../ul'
    ).text
    asistentes = context.driver.find_element(
        By.XPATH, '//*[@id="id_asistentes"]/../ul'
    ).text
    proposito = context.driver.find_element(
        By.XPATH, '//*[@id="id_proposito"]/../ul'
    ).text
    assert mensaje in sala, f'Faltó "{mensaje}" en Sala: {sala}'
    assert mensaje in fecha, f'Faltó "{mensaje}" en Fecha: {fecha}'
    assert mensaje in inicio, f'Faltó "{mensaje}" en Hora de inicio: {inicio}'
    assert mensaje in fin, f'Faltó "{mensaje}" en Hora de fin: {fin}'
    assert mensaje in asistentes, (
        f'Faltó "{mensaje}" en Asistentes: {asistentes}'
    )
    assert mensaje in proposito, (
        f'Faltó "{mensaje}" en Propósito: {proposito}'
    )
