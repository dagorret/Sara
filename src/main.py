import pandas as pd
import statsmodels.api as sm

# 1. Cargar dataset
df = pd.read_csv("datos/ejemplo.csv")

print("Dataset:")
print(df)
print("\n")

# 2. Definir variables
X = df[["educacion", "experiencia"]]  # variables explicativas
y = df["ingreso"]                    # variable dependiente

# 3. Agregar constante (intercepto)
X = sm.add_constant(X)

# 4. Ajustar modelo
modelo = sm.OLS(y, X).fit()

# 5. Resultados
print(modelo.summary())
