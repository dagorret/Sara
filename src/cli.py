import argparse
import sys
from pathlib import Path

from core.evaluation import analizar_clasificacion
from core.exporter import (
    exportar_coeficientes_csv,
    exportar_predicciones_csv,
    exportar_reporte_txt,
)
from core.loader import cargar_csv
from core.regression import correr_logit, correr_ols, correr_probit
from core.report import (
    imprimir_advertencias_modelo,
    imprimir_analisis_automatico,
    imprimir_balance_clases,
    imprimir_comparacion_modelos,
    imprimir_diagnostico_avanzado,
    imprimir_diagnostico_automatico,
    imprimir_evaluacion_clasificacion,
    imprimir_recomendacion_final,
    imprimir_reporte_validacion,
    imprimir_resumen_modelo,
)
from core.validator import ejecutar_validaciones


def parse_threshold(value):
    try:
        threshold = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "El threshold debe ser un número entre 0 y 1."
        ) from exc

    if threshold < 0 or threshold > 1:
        raise argparse.ArgumentTypeError(
            "El threshold debe estar entre 0 y 1."
        )

    return threshold


def parse_args():
    parser = argparse.ArgumentParser(
        description="SARA - Herramienta econométrica en CLI"
    )

    parser.add_argument(
        "--method",
        required=True,
        choices=["ols", "logit", "probit"],
        help="Método econométrico"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Ruta al archivo CSV"
    )
    parser.add_argument(
        "--y",
        required=True,
        help="Variable dependiente"
    )
    parser.add_argument(
        "--x",
        required=True,
        nargs="+",
        help="Variables explicativas"
    )
    parser.add_argument(
        "--threshold",
        type=parse_threshold,
        default=0.5,
        help="Threshold para clasificación binaria (default: 0.5)"
    )
    parser.add_argument(
        "--out",
        help="Ruta para exportar un reporte TXT"
    )
    parser.add_argument(
        "--out-csv",
        help="Ruta para exportar los coeficientes en CSV"
    )
    parser.add_argument(
        "--out-pred",
        help="Ruta para exportar predicciones en CSV"
    )

    return parser.parse_args()


def ejecutar_modelo(method, df, y, x):
    if method == "ols":
        return correr_ols(df, y, x)

    if method == "logit":
        return correr_logit(df, y, x)

    if method == "probit":
        return correr_probit(df, y, x)

    raise ValueError(f"Método no soportado: {method}")


def obtener_evaluacion_modelo(method, modelo, df, y, x, threshold, mensajes_modelo):
    if method not in {"logit", "probit"}:
        return None

    return analizar_clasificacion(
        modelo,
        df,
        y,
        x,
        threshold=threshold,
        mensajes_modelo=mensajes_modelo,
    )


def _construir_prefijo_auto(file_path, method):
    nombre_base = Path(file_path).stem
    return Path("resultados") / f"{nombre_base}_{method}"


def resolver_rutas_exportacion(args):
    prefijo_auto = _construir_prefijo_auto(args.file, args.method)

    out = args.out
    out_csv = args.out_csv
    out_pred = args.out_pred

    if out == "auto":
        out = f"{prefijo_auto}_reporte.txt"

    if out_csv == "auto":
        out_csv = f"{prefijo_auto}_coeficientes.csv"

    if out_pred == "auto":
        out_pred = f"{prefijo_auto}_predicciones.csv"

    return out, out_csv, out_pred


def exportar_salidas(
    method,
    out,
    out_csv,
    out_pred,
    modelo,
    errores,
    advertencias,
    mensajes_modelo,
    evaluacion,
):
    if out:
        exportar_reporte_txt(
            out,
            modelo,
            method,
            errores=errores,
            advertencias=advertencias,
            mensajes_modelo=mensajes_modelo,
            evaluacion=evaluacion,
        )
        print(f"\nReporte TXT exportado en: {out}")

    if out_csv:
        exportar_coeficientes_csv(out_csv, modelo, evaluacion=evaluacion)
        print(f"Coeficientes CSV exportados en: {out_csv}")

    if out_pred:
        exportado = exportar_predicciones_csv(out_pred, evaluacion)
        if exportado:
            print(f"Predicciones CSV exportadas en: {out_pred}")
        else:
            print("Predicciones CSV no exportadas: solo aplica a Logit/Probit.")


def main():
    args = parse_args()
    out, out_csv, out_pred = resolver_rutas_exportacion(args)
    dataset = cargar_csv(args.file)

    print("\n=== DATASET ===")
    print(dataset.get_preview())

    errores, advertencias = ejecutar_validaciones(dataset, args.y, args.x, args.method)
    imprimir_reporte_validacion(errores, advertencias)

    if errores:
        print("\nNo se puede continuar hasta corregir los errores.")
        sys.exit(1)

    modelo, mensajes_modelo = ejecutar_modelo(
        args.method,
        dataset,
        args.y,
        args.x,
    )

    evaluacion = obtener_evaluacion_modelo(
        args.method,
        modelo,
        dataset,
        args.y,
        args.x,
        args.threshold,
        mensajes_modelo,
    )

    imprimir_advertencias_modelo(mensajes_modelo)
    imprimir_resumen_modelo(modelo, args.method, mensajes_modelo)
    imprimir_evaluacion_clasificacion(evaluacion)
    imprimir_analisis_automatico(evaluacion)
    imprimir_diagnostico_automatico(evaluacion)
    imprimir_comparacion_modelos(evaluacion)
    imprimir_balance_clases(evaluacion)
    imprimir_diagnostico_avanzado(evaluacion)
    imprimir_recomendacion_final(evaluacion)
    exportar_salidas(
        args.method,
        out,
        out_csv,
        out_pred,
        modelo,
        errores,
        advertencias,
        mensajes_modelo,
        evaluacion,
    )


if __name__ == "__main__":
    main()
