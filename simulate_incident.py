"""
Script CLI para simular incidentes de produccion y evaluar la respuesta del agente SRE.
"""

import sys
import argparse
from src.scenarios.incident_catalogue import INCIDENTS
from src.agents.incident_agent import analyze_incident


def print_banner(text: str):
    print("\n" + "=" * 75)
    print(f"  {text}")
    print("=" * 75)


def run_simulation(scenario_key: str):
    if scenario_key not in INCIDENTS:
        print(f"Error: Escenario '{scenario_key}' no encontrado.")
        print(f"Escenarios disponibles: {', '.join(INCIDENTS.keys())}")
        sys.exit(1)

    alert = INCIDENTS[scenario_key]

    print_banner(f"ALERTA RECIBIDA: [{alert.severity}] {alert.id}")
    print(f"Servicio:   {alert.service}")
    print(f"Origen:     {alert.source} | Entorno: {alert.environment}")
    print(f"Titulo:     {alert.title}")
    print(f"Resumen:    {alert.summary}")

    print("\nMetricas Clave:")
    for k, v in alert.metrics.items():
        print(f"  - {k}: {v}")

    print("\nUltimos Logs del Servicio:")
    for log in alert.logs:
        print(f"  {log}")

    print("\nEventos del Cluster Kubernetes:")
    for ev in alert.k8s_events:
        print(f"  {ev}")

    print_banner("INICIANDO ANALISIS CON AGENTE AIOps (LiteLLM / Bedrock)")
    print("Procesando telemetria y calculando causa raiz (RCA)...")

    diagnosis = analyze_incident(alert)

    print_banner("DIAGNOSTICO Y PLAN DE REMEDIACION GENERADO")
    print(f"ID Incidente:       {diagnosis.incident_id}")
    print(f"Severidad Evaluada: {diagnosis.evaluated_severity}")
    print(f"Indice de Confianza: {int(diagnosis.confidence_score * 100)}%")
    print(f"\nRadio de Explosion (Blast Radius):\n  {diagnosis.blast_radius}")
    print(f"\nAnalisis Causa Raiz (RCA):\n  {diagnosis.root_cause_analysis}")

    print("\nPlan de Mitigacion Inmediata (Runbook):")
    for step in diagnosis.immediate_actions:
        print(f"\n  [Paso {step.order}] {step.action}")
        if step.command:
            print(f"  Comando: {step.command}")
        print(f"  Resultado Esperado: {step.expected_outcome}")

    print("\nMedidas Preventivas Post-Mortem:")
    for p in diagnosis.preventative_measures:
        print(f"  - {p}")

    print_banner("SIMULACION DE INCIDENTE FINALIZADA")


def main():
    parser = argparse.ArgumentParser(description="Simulador de Incidentes SRE con LiteLLM y Amazon Bedrock")
    parser.add_argument(
        "--scenario",
        choices=["oom-killed", "db-connection-pool", "canary-500-cascade", "all"],
        default="oom-killed",
        help="Escenario de incidente a ejecutar (por defecto: oom-killed)"
    )
    args = parser.parse_args()

    if args.scenario == "all":
        for key in INCIDENTS.keys():
            run_simulation(key)
    else:
        run_simulation(args.scenario)


if __name__ == "__main__":
    main()
