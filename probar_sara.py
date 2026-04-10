#!/usr/bin/env python3
"""
Suite de pruebas para SARA.

Qué hace:
- Ejecuta casos sanos y patológicos para OLS / Logit / Probit
- Prueba thresholds
- Prueba exportación
- Prueba errores controlados
- Guarda un reporte de texto con stdout/stderr/exit code de cada prueba

Uso:
    source .venv/bin/activate
    python probar_sara.py

Opcionales:
    python probar_sara.py --python python
    python probar_sara.py --cli src/cli.py
    python probar_sara.py --out reporte.txt
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class TestCase:
    nombre: str
    comando: List[str]
    descripcion: str
    esperado: List[str]


def run_case(case: TestCase, workdir: Path) -> dict:
    proc = subprocess.run(
        case.comando,
        cwd=workdir,
        capture_output=True,
        text=True,
    )
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()

    contenido = stdout + ("\n" + stderr if stderr else "")
    faltantes = [txt for txt in case.esperado if txt not in contenido]
    ok = proc.returncode == 0 and not faltantes

    return {
        "nombre": case.nombre,
        "descripcion": case.descripcion,
        "comando": " ".join(shlex.quote(x) for x in case.comando),
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "faltantes": faltantes,
        "ok": ok,
    }


def run_case_expect_fail(case: TestCase, workdir: Path) -> dict:
    proc = subprocess.run(
        case.comando,
        cwd=workdir,
        capture_output=True,
        text=True,
    )
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()

    contenido = stdout + ("\n" + stderr if stderr else "")
    faltantes = [txt for txt in case.esperado if txt not in contenido]
    ok = proc.returncode != 0 and not faltantes

    return {
        "nombre": case.nombre,
        "descripcion": case.descripcion,
        "comando": " ".join(shlex.quote(x) for x in case.comando),
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "faltantes": faltantes,
        "ok": ok,
    }


def validar_exportacion(workdir: Path) -> dict:
    reporte_exportado = workdir / "resultados" / "logit_grande_logit_reporte.txt"

    esperado = [
        "Evaluación del modelo:",
        "Análisis automático:",
        "Comparación de modelos:",
        "Balance de clases:",
        "Diagnóstico avanzado:",
        "Recomendación final:",
    ]

    if not reporte_exportado.exists():
        return {
            "nombre": "Validación reporte exportado",
            "descripcion": "Verifica que el TXT exportado incluya los bloques nuevos.",
            "comando": "verificación interna de archivo exportado",
            "returncode": 1,
            "stdout": "",
            "stderr": f"No existe el archivo: {reporte_exportado}",
            "faltantes": esperado,
            "ok": False,
        }

    contenido = reporte_exportado.read_text(encoding="utf-8")
    faltantes = [txt for txt in esperado if txt not in contenido]

    return {
        "nombre": "Validación reporte exportado",
        "descripcion": "Verifica que el TXT exportado incluya los bloques nuevos.",
        "comando": "verificación interna de archivo exportado",
        "returncode": 0 if not faltantes else 1,
        "stdout": contenido,
        "stderr": "",
        "faltantes": faltantes,
        "ok": not faltantes,
    }


def build_cases(py: str, cli: str) -> tuple[list[TestCase], list[TestCase]]:
    cases_ok = [
        TestCase(
            "OLS chico",
            [py, cli, "--method", "ols", "--file", "datos/ejemplo.csv", "--y", "ingreso", "--x", "educacion", "experiencia"],
            "Verifica que OLS chico siga funcionando.",
            ["Método: Mínimos Cuadrados Ordinarios (OLS)", "R-cuadrado:", "Interpretación rápida:"],
        ),
        TestCase(
            "OLS grande",
            [py, cli, "--method", "ols", "--file", "datos/ols_grande.csv", "--y", "ingreso", "--x", "educacion", "experiencia"],
            "Verifica que OLS grande no se rompa con la analítica nueva.",
            ["Método: Mínimos Cuadrados Ordinarios (OLS)", "R-cuadrado:", "Número de condición:"],
        ),
        TestCase(
            "Logit sano threshold 0.5",
            [py, cli, "--method", "logit", "--file", "datos/logit_grande.csv", "--y", "aprobado", "--x", "horas_estudio", "asistencia", "--threshold", "0.5"],
            "Caso sano de clasificación.",
            ["Accuracy:", "Precision:", "Recall:", "F1:", "AUC:", "COMPARACIÓN DE MODELOS", "BALANCE DE CLASES"],
        ),
        TestCase(
            "Probit sano threshold 0.5",
            [py, cli, "--method", "probit", "--file", "datos/logit_grande.csv", "--y", "aprobado", "--x", "horas_estudio", "asistencia", "--threshold", "0.5"],
            "Caso sano con probit.",
            ["Accuracy:", "Precision:", "Recall:", "F1:", "AUC:", "COMPARACIÓN DE MODELOS"],
        ),
        TestCase(
            "Logit patológico",
            [py, cli, "--method", "logit", "--file", "datos/ejemplo2.csv", "--y", "aprobado", "--x", "horas_estudio", "asistencia", "--threshold", "0.5"],
            "Debe detectar separación perfecta / invalidez.",
            ["Separación perfecta detectada", "Modelo inválido", "COMPARACIÓN DE MODELOS"],
        ),
        TestCase(
            "Probit patológico",
            [py, cli, "--method", "probit", "--file", "datos/ejemplo2.csv", "--y", "aprobado", "--x", "horas_estudio", "asistencia", "--threshold", "0.5"],
            "Debe detectar separación perfecta / invalidez con probit.",
            ["Separación perfecta detectada", "Modelo inválido", "COMPARACIÓN DE MODELOS"],
        ),
        TestCase(
            "Logit threshold 0.1",
            [py, cli, "--method", "logit", "--file", "datos/logit_grande.csv", "--y", "aprobado", "--x", "horas_estudio", "asistencia", "--threshold", "0.1"],
            "Debe favorecer recall y aumentar falsos positivos.",
            ["Threshold usado: 0.1000", "Recall:", "Matriz de confusión:", "Mejor threshold sugerido:"],
        ),
        TestCase(
            "Logit threshold 0.9",
            [py, cli, "--method", "logit", "--file", "datos/logit_grande.csv", "--y", "aprobado", "--x", "horas_estudio", "asistencia", "--threshold", "0.9"],
            "Debe favorecer precision y aumentar falsos negativos.",
            ["Threshold usado: 0.9000", "Precision:", "Matriz de confusión:", "Mejor threshold sugerido:"],
        ),
        TestCase(
            "Exportación AUTO",
            [py, cli, "--method", "logit", "--file", "datos/logit_grande.csv", "--y", "aprobado", "--x", "horas_estudio", "asistencia", "--threshold", "0.5", "--out", "auto", "--out-csv", "auto", "--out-pred", "auto"],
            "Debe exportar reporte y CSVs con nombres automáticos.",
            ["Reporte TXT exportado en:", "Coeficientes CSV exportados en:", "Predicciones CSV exportadas en:"],
        ),
    ]

    cases_fail = [
        TestCase(
            "Error por columna inexistente",
            [py, cli, "--method", "logit", "--file", "datos/logit_grande.csv", "--y", "aprobadoo", "--x", "horas_estudio", "asistencia"],
            "Debe cortar limpio por columna inexistente.",
            ["Faltan columnas en el dataset", "No se puede continuar hasta corregir los errores."],
        ),
        TestCase(
            "Error por threshold inválido",
            [py, cli, "--method", "logit", "--file", "datos/logit_grande.csv", "--y", "aprobado", "--x", "horas_estudio", "asistencia", "--threshold", "1.2"],
            "Debe rechazar threshold fuera de [0, 1].",
            ["El threshold debe estar entre 0 y 1."],
        ),
    ]
    return cases_ok, cases_fail


def write_report(results_ok: list[dict], results_fail: list[dict], out_path: Path) -> None:
    lines: list[str] = []
    lines.append("REPORTE DE PRUEBAS - SARA")
    lines.append("=" * 80)
    total = len(results_ok) + len(results_fail)
    passed = sum(1 for r in results_ok if r["ok"]) + sum(1 for r in results_fail if r["ok"])
    lines.append(f"Total de pruebas: {total}")
    lines.append(f"Pruebas OK: {passed}")
    lines.append(f"Pruebas fallidas: {total - passed}")
    lines.append("")

    def add_section(title: str, items: list[dict]) -> None:
        lines.append(title)
        lines.append("-" * 80)
        for i, r in enumerate(items, 1):
            estado = "OK" if r["ok"] else "FAIL"
            lines.append(f"[{i}] {r['nombre']} -> {estado}")
            lines.append(f"Descripción: {r['descripcion']}")
            lines.append(f"Comando: {r['comando']}")
            lines.append(f"Exit code: {r['returncode']}")
            if r["faltantes"]:
                lines.append("Textos esperados faltantes:")
                for f in r["faltantes"]:
                    lines.append(f"  - {f}")
            lines.append("")
            lines.append("STDOUT:")
            lines.append(r["stdout"] or "<vacío>")
            lines.append("")
            lines.append("STDERR:")
            lines.append(r["stderr"] or "<vacío>")
            lines.append("")
            lines.append("=" * 80)
            lines.append("")

    add_section("PRUEBAS QUE DEBEN FUNCIONAR", results_ok)
    add_section("PRUEBAS QUE DEBEN FALLAR DE FORMA CONTROLADA", results_fail)

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Suite de pruebas para SARA")
    parser.add_argument("--python", default=sys.executable, help="Intérprete de Python a usar")
    parser.add_argument("--cli", default="src/cli.py", help="Ruta al CLI de SARA")
    parser.add_argument("--out", default="reporte.txt", help="Ruta del reporte de salida")
    args = parser.parse_args()

    workdir = Path.cwd()
    out_path = (workdir / args.out).resolve()

    cases_ok, cases_fail = build_cases(args.python, args.cli)

    results_ok = [run_case(case, workdir) for case in cases_ok]
    results_ok.append(validar_exportacion(workdir))
    results_fail = [run_case_expect_fail(case, workdir) for case in cases_fail]

    write_report(results_ok, results_fail, out_path)

    print(f"Reporte generado en: {out_path}")
    total = len(results_ok) + len(results_fail)
    passed = sum(1 for r in results_ok if r["ok"]) + sum(1 for r in results_fail if r["ok"])
    print(f"Resumen: {passed}/{total} pruebas OK")

    failed_names = [r["nombre"] for r in results_ok + results_fail if not r["ok"]]
    if failed_names:
        print("Pruebas fallidas:")
        for name in failed_names:
            print(f" - {name}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
