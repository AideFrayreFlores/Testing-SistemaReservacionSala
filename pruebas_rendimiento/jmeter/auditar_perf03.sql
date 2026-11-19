-- Antes de ejecutar: SET @fecha_base = 'AAAA-MM-DD';
-- Verificación de solo lectura: cada ronda debe dejar una fila vigente.
WITH RECURSIVE rondas AS (
    SELECT 1 AS ronda, CAST(@fecha_base AS DATE) AS fecha
    UNION ALL
    SELECT ronda + 1, DATE_ADD(fecha, INTERVAL 1 DAY)
    FROM rondas
    WHERE ronda < 10
)
SELECT rondas.ronda, rondas.fecha, COUNT(r.id) AS vigentes_persistidas
FROM rondas
LEFT JOIN reservaciones_reservacion AS r
  ON r.fecha = rondas.fecha
 AND r.sala_id = 1
 AND r.hora_inicio = '08:00:00'
 AND r.hora_fin = '09:00:00'
 AND r.estado = 'VIGENTE'
 AND r.proposito = CONCAT('Reserva PERF-03 ronda ',
                          LPAD(rondas.ronda, 2, '0'), ' de 10 ',
                          rondas.fecha, ' 08:00-09:00')
GROUP BY rondas.ronda, rondas.fecha
ORDER BY rondas.ronda;
