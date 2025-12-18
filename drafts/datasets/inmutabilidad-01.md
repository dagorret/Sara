1) ¿Cada fila puede ser transformada por una expresión matemática o algoritmo predefinido?
✔ Sí, con una condición clave

Las transformaciones deben ser:

declarativas

determinísticas

versionadas

Qué significa en la práctica

Una transformación es algo del tipo:

ingreso_real = ingreso_nominal / ipc

log_ingreso = log(ingreso)

edad_grupo = CASE WHEN edad < 18 THEN 0 ELSE 1 END

winsorización

normalización

discretización

Técnicamente:

se expresa como SQL (DuckDB) o

como función predefinida del sistema (no código libre del usuario en V1)

Cómo se registra

Cada transformación queda como una Operation:

{
  "operation_type": "transform",
  "parameters": {
    "expression": "log(ingreso)"
  },
  "input_version_id": 3,
  "output_version_id": 4
}


👉 Nunca se modifica una fila “en el lugar”
👉 Se genera una nueva versión del dataset

2) ¿Pueden ser listados con filtros, conteo y muestra de hasta 100?
✔ Sí, y es obligatorio que sea así

Esto es UX + performance + seguridad.

Operaciones permitidas

Filtros (WHERE edad >= 18)

Conteos (COUNT(*))

Estadísticas simples

Preview limitado (LIMIT 100)

Todo esto:

se ejecuta en DuckDB

sin cargar todo el dataset en RAM

sin exponer millones de filas en la UI

Ejemplo técnico
SELECT *
FROM data
WHERE provincia = 'Córdoba'
LIMIT 100;


Y en paralelo:

SELECT COUNT(*)
FROM data
WHERE provincia = 'Córdoba';


👉 Mostrar muestra + conteo total es el patrón correcto.

3) ¿Pueden ser reemplazados los elementos [x] = y?
✔ Sí, pero no como edición directa

El reemplazo se hace como operación declarativa, no como “edición manual”.

Ejemplos válidos

sexo = 'M' → 1

NA → 0

categoria = 'A' → 'Alta'

Implementación típica:

CASE
  WHEN sexo = 'M' THEN 1
  WHEN sexo = 'F' THEN 0
  ELSE NULL
END AS sexo_recod


Esto:

crea una nueva columna o

reemplaza una columna en una nueva versión
