from behave import given, when, then
from behave.api.pending_step import StepNotImplementedError


@given(u'que ingreso al sistema de reservaciones')
def step_impl(context):
    raise StepNotImplementedError(
        u'Given que ingreso al sistema de reservaciones'
    )


@given(u'escribo el usuario "alumno1" y la contraseña "alumno123"')
def step_impl(context):
    raise StepNotImplementedError(
        u'Given escribo el usuario "alumno1" y la contraseña "alumno123"'
    )


@given(u'presiono el botón Ingresar')
def step_impl(context):
    raise StepNotImplementedError(u'Given presiono el botón Ingresar')


@given(u'doy click en el botón Nueva reservación')
def step_impl(context):
    raise StepNotImplementedError(
        u'Given doy click en el botón Nueva reservación'
    )


@given(u'selecciono la sala "Sala A"')
def step_impl(context):
    raise StepNotImplementedError(u'Given selecciono la sala "Sala A"')


@given(
    u'capturo la fecha "2027-05-20", hora de inicio "10:00" '
    u'y hora de fin "11:00"'
)
def step_impl(context):
    raise StepNotImplementedError(
        u'Given capturo la fecha "2027-05-20", hora de inicio "10:00" '
        u'y hora de fin "11:00"'
    )


@given(
    u'capturo el número de asistentes "3" '
    u'y el propósito "Estudio grupal para examen"'
)
def step_impl(context):
    raise StepNotImplementedError(
        u'Given capturo el número de asistentes "3" '
        u'y el propósito "Estudio grupal para examen"'
    )


@when(u'presiono el botón Guardar reservación')
def step_impl(context):
    raise StepNotImplementedError(u'When presiono el botón Guardar reservación')


@then(
    u'puedo ver el mensaje de confirmación '
    u'"Reservación registrada exitosamente."'
)
def step_impl(context):
    raise StepNotImplementedError(
        u'Then puedo ver el mensaje de confirmación '
        u'"Reservación registrada exitosamente."'
    )
