# Correcciones tras la retroalimentación de la Entrega 1

## Observación del profesor
Al registrar una salida, el código unía la nota de entrada y la de salida en un solo campo de
255 caracteres y recortaba el resultado. Si la nota de entrada ya ocupaba ese espacio, la nota
de salida se perdía por completo aunque el sistema confirmara el registro. Esto incumplía el
criterio de aceptación de la HU-03 («las observaciones de la salida se agregan a las de la
entrada, sin perderlas»).

## Corrección realizada
| Aspecto | Antes | Ahora |
|---|---|---|
| Base de datos | `movimiento.observaciones` VARCHAR(255) | `observaciones_entrada` y `observaciones_salida`, VARCHAR(255) cada una |
| Registro de salida | Concatenaba ambas notas y recortaba a 255 | Guarda la nota de salida en su propio campo; no toca la de entrada |
| Nota demasiado larga | Se recortaba en silencio | Se **rechaza** con un mensaje claro (máx. 255 caracteres) y no se registra nada a medias |
| Historial | Una sola columna «Observaciones» | Muestra «Entrada: …» y «Salida: …» por separado |
| Modelos | MER, MR, físico y clases con un solo campo | Actualizados con los dos campos |

## Pruebas agregadas (de 21 a 30)
1. `test_salida_conserva_ambas_notas_aunque_la_de_entrada_ocupe_el_maximo`: entrada de 255 + salida de 255 caracteres, releídas desde la base de datos.
2. `test_salida_sin_nota_no_altera_la_de_entrada`.
3. `test_nota_demasiado_larga_se_rechaza_en_vez_de_recortarse` (entrada y salida; verifica que no queda nada a medias).
4. Rutas: mensaje de error con nota de 300 caracteres y el historial muestra ambas notas.
5. Concurrencia (`tests/test_concurrencia.py`, 4 pruebas con hilos): 8 operarios registrando la misma placa a la vez, dos vehículos pidiendo la misma celda, asignación automática simultánea y salida simultánea. Verifican que nunca hay más de un movimiento abierto por vehículo ni por celda. Se pueden ejecutar sobre MySQL (ver README).

## Ajuste adicional
Los datos de ejemplo pasan a 80 celdas: 70 de carro (C-01 a C-70) y 10 de moto (M-01 a M-10).
