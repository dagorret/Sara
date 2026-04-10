import pandas as pd
import numpy as np

np.random.seed(42)

n = 10000

horas = np.random.randint(0, 10, n)
asistencia = np.random.randint(50, 100, n)

# probabilidad (NO perfecta → importante)
z = -5 + 0.8 * horas + 0.05 * asistencia
prob = 1 / (1 + np.exp(-z))

aprobado = np.random.binomial(1, prob)

df = pd.DataFrame({
    "aprobado": aprobado,
    "horas_estudio": horas,
    "asistencia": asistencia
})

df.to_csv("datos/logit_grande.csv", index=False)

print("CSV generado: datos/logit_grande.csv")
