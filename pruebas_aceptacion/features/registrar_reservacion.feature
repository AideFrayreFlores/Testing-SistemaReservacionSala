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
