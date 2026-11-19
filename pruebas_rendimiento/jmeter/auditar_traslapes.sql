-- Auditoría de solo lectura de la integridad de las reservaciones.
-- Cada pareja se cuenta una sola vez. Los horarios contiguos no se traslapan.
SELECT COUNT(*) AS pares_vigentes_traslapados
FROM reservaciones_reservacion AS primera
JOIN reservaciones_reservacion AS segunda
  ON primera.id < segunda.id
 AND primera.sala_id = segunda.sala_id
 AND primera.fecha = segunda.fecha
 AND primera.hora_inicio < segunda.hora_fin
 AND segunda.hora_inicio < primera.hora_fin
WHERE primera.estado = 'VIGENTE'
  AND segunda.estado = 'VIGENTE';
