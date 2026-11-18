import os
from selenium import webdriver

from fixture_ca09 import limpiar as limpiar_reserva_ca09


def crear_driver():
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
    driver.set_window_size(1400, 900)
    driver.implicitly_wait(5)
    return driver


def _cerrar_driver(driver):
    try:
        driver.quit()
    except Exception:
        pass


def before_scenario(context, scenario):
    context.base_url = os.getenv('BASE_URL', 'http://localhost:8000')
    context.crear_driver = crear_driver
    context.driver = None
    context.drivers = []
    context.reserva_ca09_id = None


def after_scenario(context, scenario):
    if getattr(context, 'driver', None) is not None:
        _cerrar_driver(context.driver)
        context.driver = None
    for driver in getattr(context, 'drivers', []):
        _cerrar_driver(driver)
    context.drivers = []
    if getattr(context, 'reserva_ca09_id', None) is not None:
        limpiar_reserva_ca09(context.reserva_ca09_id)
