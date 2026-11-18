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

    Escenario: CA-08 Impedir que un usuario cancele una reservación ajena
        Dado que ingreso al sistema de reservaciones
        Y escribo el usuario "alumno1" y la contraseña "alumno123"
        Y presiono el botón Ingresar
        Y preparo un horario futuro de prueba en "Sala A"
        Y registro una reservación en ese horario con propósito "Reservación ajena CA-08"
        Y recuerdo la acción de cancelar de la reservación "Reservación ajena CA-08"
        Dado que cierro sesión
        Y escribo el usuario "alumno2" y la contraseña "alumno567"
        Y presiono el botón Ingresar
        Entonces la reservación "Reservación ajena CA-08" no aparece en mi lista
        Y no veo la acción de cancelar de la reservación recordada
        Cuando envío una petición POST de cancelación a la acción recordada
        Entonces puedo ver el mensaje de rechazo "No tienes permiso para cancelar esta reservación."
        Y el rechazo no revela el propósito "Reservación ajena CA-08"
        Y guardo una captura llamada "CA08_rechazo_reservacion_ajena.png"
        Dado que cierro sesión
        Y escribo el usuario "alumno1" y la contraseña "alumno123"
        Y presiono el botón Ingresar
        Entonces la reservación "Reservación ajena CA-08" sigue vigente con su acción de cancelar
        Y guardo una captura llamada "CA08_reservacion_ajena_intacta.png"

    Escenario: CA-09 Impedir la cancelación fuera del periodo permitido
        Dado que preparo una reservación que inicia en 30 minutos
        Y que ingreso al sistema de reservaciones
        Y escribo el usuario "alumno1" y la contraseña "alumno123"
        Y presiono el botón Ingresar
        Entonces la reservación "Aceptación HU-02 CA-09 fuera del periodo" no muestra la acción de cancelar
        Y la reservación "Aceptación HU-02 CA-09 fuera del periodo" muestra el aviso "El periodo de cancelación ha concluido."
        Cuando envío una petición POST de cancelación a la acción recordada
        Entonces puedo ver el mensaje de rechazo "El periodo de cancelación ha concluido."
        Y la reservación "Aceptación HU-02 CA-09 fuera del periodo" sigue vigente sin acción de cancelar
        Y guardo una captura llamada "CA09_rechazo_periodo_concluido.png"
