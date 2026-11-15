from time import sleep
from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


@given(u'que ingreso al sistema de reservaciones')
def step_impl(context):
    context.driver = webdriver.Chrome()
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
    campo_fecha = context.driver.find_element(By.ID, 'id_fecha')
    campo_fecha.clear()
    context.driver.execute_script(
        "arguments[0].value = arguments[1];",
        campo_fecha,
        fecha
    )
    campo_inicio = context.driver.find_element(By.ID, 'id_hora_inicio')
    campo_inicio.clear()
    context.driver.execute_script(
        "arguments[0].value = arguments[1];",
        campo_inicio,
        inicio
    )
    campo_fin = context.driver.find_element(By.ID, 'id_hora_fin')
    campo_fin.clear()
    context.driver.execute_script(
        "arguments[0].value = arguments[1];",
        campo_fin,
        fin
    )
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
