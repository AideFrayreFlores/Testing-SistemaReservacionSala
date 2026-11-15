from time import sleep
from behave import given
from selenium.webdriver.common.by import By


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
