Característica: Cancelar una reservación
    Como usuario autenticado propietario de una reservación
    Quiero cancelar una reservación que ya no utilizaré
    Para liberar la sala y permitir que otro usuario pueda reservarla.

    Escenario: CA-07 Cancelar con anticipación y volver a reservar el mismo horario
        Dado que ingreso al sistema de reservaciones
        Y escribo el usuario "alumno1" y la contraseña "alumno123"
        Y presiono el botón Ingresar
        Y preparo un horario futuro de prueba en "Sala A"
        Y registro una reservación en ese horario con propósito "Estudio para CA-07"
        Cuando confirmo la cancelación de la reservación "Estudio para CA-07"
        Entonces puedo ver el mensaje de confirmación "Reservación cancelada exitosamente."
        Y la reservación "Estudio para CA-07" aparece cancelada con fecha y hora
        Cuando registro otra reservación en el mismo horario con propósito "Reutilización para CA-07"
        Entonces puedo ver el mensaje de confirmación "Reservación registrada exitosamente."
        Y la reservación "Reutilización para CA-07" aparece vigente
