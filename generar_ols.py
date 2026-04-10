import pandas as pd
import numpy as np

np.random.seed(42)

n = 10000

educacion = np.random.randint(5, 20, n)
experiencia = np.random.randint(0, 30, n)

# modelo real (con ruido)
ingreso = 200 + 120 * educacion + 10 * experiencia + np.random.normal(0, 200, n)

df = pd.DataFrame({
    "ingreso": ingreso,
    "educacion": educacion,
    "experiencia": experiencia
})

df.to_csv("datos/ols_grande.csv", index=False)

print("CSV generado: datos/ols_grande.csv")
