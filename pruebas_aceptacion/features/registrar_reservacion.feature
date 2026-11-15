Característica: Registrar una reservación
    Como usuario autenticado
    Quiero reservar una sala de estudio indicando fecha, horario, número de asistentes y propósito
    Para apartar un espacio disponible y utilizarlo en una actividad académica.

    Escenario: Registro exitoso de reservación
        Dado que ingreso al sistema de reservaciones
        Y escribo el usuario "alumno1" y la contraseña "alumno123"
        Y presiono el botón Ingresar
        Y doy click en el botón Nueva reservación
        Y selecciono la sala "Sala A"
        Y capturo la fecha "2027-05-20", hora de inicio "10:00" y hora de fin "11:00"
        Y capturo el número de asistentes "3" y el propósito "Estudio grupal para examen"
        Cuando presiono el botón Guardar reservación
        Entonces puedo ver el mensaje de confirmación "Reservación registrada exitosamente."

    Escenario: Rechazo por traslape de horario
        Dado que ingreso al sistema de reservaciones
        Y escribo el usuario "alumno1" y la contraseña "alumno123"
        Y presiono el botón Ingresar
        Y doy click en el botón Nueva reservación
        Y selecciono la sala "Sala A"
        Y capturo la fecha "2027-05-20", hora de inicio "10:30" y hora de fin "11:30"
        Y capturo el número de asistentes "3" y el propósito "Asesoría de proyecto final"
        Cuando presiono el botón Guardar reservación
        Entonces puedo ver el mensaje de error "La sala no está disponible en el horario solicitado."

    Escenario: Rechazo por capacidad excedida
        Dado que ingreso al sistema de reservaciones
        Y escribo el usuario "alumno2" y la contraseña "alumno567"
        Y presiono el botón Ingresar
        Y doy click en el botón Nueva reservación
        Y selecciono la sala "Sala A"
        Y capturo la fecha "2027-05-21", hora de inicio "13:00" y hora de fin "13:40"
        Y capturo el número de asistentes "5" y el propósito "Reunión de equipo de software"
        Cuando presiono el botón Guardar reservación
        Entonces puedo ver el mensaje de error en el formulario "El número de asistentes supera la capacidad de la sala."

    Escenario: Rechazo por fecha inválida
        Dado que ingreso al sistema de reservaciones
        Y escribo el usuario "alumno1" y la contraseña "alumno123"
        Y presiono el botón Ingresar
        Y doy click en el botón Nueva reservación
        Y selecciono la sala "Sala C"
        Y capturo la fecha "2020-01-10", hora de inicio "10:00" y hora de fin "11:00"
        Y capturo el número de asistentes "3" y el propósito "Estudio grupal para examen"
        Cuando presiono el botón Guardar reservación
        Entonces puedo ver el mensaje de error de validación "La fecha no puede ser anterior al día actual."

    Escenario: Rechazo por fecha y horario inválidos
        Dado que ingreso al sistema de reservaciones
        Y escribo el usuario "alumno2" y la contraseña "alumno567"
        Y presiono el botón Ingresar
        Y doy click en el botón Nueva reservación
        Y selecciono la sala "Sala B"
        Y capturo la fecha "2020-01-10", hora de inicio "12:00" y hora de fin "11:00"
        Y capturo el número de asistentes "3" y el propósito "Estudio grupal para examen"
        Cuando presiono el botón Guardar reservación
        Entonces puedo ver los mensajes de error de fecha "La fecha no puede ser anterior al día actual." y de horario "La hora de fin debe ser posterior a la hora de inicio."

    Escenario: Rechazo por fecha y horario inválidos
        Dado que ingreso al sistema de reservaciones
        Y escribo el usuario "alumno1" y la contraseña "alumno123"
        Y presiono el botón Ingresar
        Y doy click en el botón Nueva reservación
        Y selecciono la sala "Sala A"
        Y capturo la fecha "2020-01-10", hora de inicio "12:00" y hora de fin "11:00"
        Y capturo el número de asistentes "3" y el propósito "Estudio grupal para examen"
        Cuando presiono el botón Guardar reservación
        Entonces puedo ver los mensajes de error de fecha "La fecha no puede ser anterior al día actual." y de horario "La hora de fin debe ser posterior a la hora de inicio."
