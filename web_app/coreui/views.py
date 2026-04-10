from django.shortcuts import render
import pandas as pd

from core.evaluation import evaluar_clasificacion
from core.regression import correr_logit, correr_ols, correr_probit


def _normalizar_resultado_modelo(resultado):
    if isinstance(resultado, tuple):
        if len(resultado) == 2:
            return resultado
        if len(resultado) == 1:
            return resultado[0], []

    return resultado, []


def _construir_interpretacion_ols(coeficientes):
    interpretacion = []

    for variable, coeficiente in coeficientes.items():
        if variable == "const":
            continue

        if coeficiente > 0:
            efecto = "efecto positivo"
        elif coeficiente < 0:
            efecto = "efecto negativo"
        else:
            efecto = "efecto nulo"

        interpretacion.append(
            f"{variable}: {efecto} ({coeficiente:.2f}) sobre la variable dependiente"
        )

    return interpretacion


def home(request):
    resultado = None

    if request.method == "POST":
        archivo = request.FILES.get("archivo")
        y = request.POST.get("y")
        x = request.POST.get("x")
        metodo = request.POST.get("metodo")

        if archivo:
            df = pd.read_csv(archivo)
            x_cols = [col.strip() for col in x.split(",") if col.strip()]

            if metodo == "ols":
                modelo, _ = _normalizar_resultado_modelo(correr_ols(df, y, x_cols))
                coeficientes = modelo.params.to_dict()

                resultado = {
                    "tipo": "ols",
                    "coeficientes": coeficientes,
                    "interpretacion": _construir_interpretacion_ols(coeficientes),
                }

            elif metodo == "logit":
                modelo, mensajes = _normalizar_resultado_modelo(
                    correr_logit(df, y, x_cols)
                )
                evaluacion = evaluar_clasificacion(modelo, df, y, x_cols)

                resultado = {
                    "tipo": "clasificacion",
                    "metodo": "logit",
                    "coeficientes": modelo.params.to_dict(),
                    "mensajes_modelo": mensajes,
                    "accuracy": evaluacion["accuracy"],
                    "precision": evaluacion["precision"],
                    "recall": evaluacion["recall"],
                    "f1": evaluacion["f1"],
                    "auc": evaluacion["auc"],
                }

            elif metodo == "probit":
                modelo, mensajes = _normalizar_resultado_modelo(
                    correr_probit(df, y, x_cols)
                )
                evaluacion = evaluar_clasificacion(modelo, df, y, x_cols)

                resultado = {
                    "tipo": "clasificacion",
                    "metodo": "probit",
                    "coeficientes": modelo.params.to_dict(),
                    "mensajes_modelo": mensajes,
                    "accuracy": evaluacion["accuracy"],
                    "precision": evaluacion["precision"],
                    "recall": evaluacion["recall"],
                    "f1": evaluacion["f1"],
                    "auc": evaluacion["auc"],
                }

    return render(request, "home.html", {"resultado": resultado})
