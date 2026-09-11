"""
Catalogo de escenarios de incidentes realistas para pruebas y simulaciones SRE.
"""

from typing import Dict
from src.models import IncidentAlert

INCIDENTS: Dict[str, IncidentAlert] = {
    "oom-killed": IncidentAlert(
        id="INC-2026-001",
        title="Microservicio de Pagos experimenta reinicios continuos (OOMKilled)",
        severity="P1-Critica",
        service="payments-processor",
        environment="production",
        source="Prometheus Alertmanager",
        summary="La tasa de reinicios del pod payments-processor supero el umbral critico (12 reinicios en 15 min).",
        metrics={
            "memory_usage_bytes": "536870912 / 536870912 (100% del limit 512Mi)",
            "cpu_throttling_percentage": "14.2%",
            "failed_transactions_per_second": "128.5",
            "pod_restarts_15m": 12
        },
        logs=[
            "2026-09-10T20:12:00Z level=info msg='Processing batch payment payload size=4.2MB'",
            "2026-09-10T20:12:15Z level=warn msg='GC pause time exceeds 1200ms'",
            "2026-09-10T20:12:45Z level=error msg='java.lang.OutOfMemoryError: Java heap space'",
            "2026-09-10T20:12:50Z level=fatal msg='Process terminated by OS signal SIGKILL (Exit code 137)'"
        ],
        k8s_events=[
            "Warning OOMKilled 2m ago kubelet, oke-pool1-node-01: Pod exceeded memory limit (512Mi)",
            "Warning BackOff 1m ago kubelet, oke-pool1-node-01: Back-off restarting failed container"
        ]
    ),
    "db-connection-pool": IncidentAlert(
        id="INC-2026-002",
        title="Agotamiento del Connection Pool de Base de Datos y Degradacion de Latencia P99",
        severity="P2-Alta",
        service="auth-service",
        environment="production",
        source="Azure Monitor",
        summary="La latencia P99 del servicio auth-service se elevo de 45ms a 4800ms tras saturacion de conexiones PostgreSQL.",
        metrics={
            "p99_latency_ms": 4850,
            "p50_latency_ms": 820,
            "active_db_connections": "100 / 100 (Max pool size alcanzado)",
            "pending_connection_wait_queue": "342 solicitudes en cola",
            "http_504_error_rate": "8.4%"
        },
        logs=[
            "2026-09-10T20:20:00Z level=warn msg='Connection checkout took 4210ms from pool HikariCP-Auth'",
            "2026-09-10T20:20:10Z level=error msg='Timeout waiting for idle connection from pool after 5000ms'",
            "2026-09-10T20:20:15Z level=error msg='HTTP 504 Gateway Timeout returned to client api-gateway'"
        ],
        k8s_events=[
            "Normal ScalingReplicaSet 5m ago deployment-controller: Scaled up replica set auth-service from 3 to 6",
            "Warning Unhealthy 1m ago kubelet: Readiness probe failed: HTTP probe failed with statuscode: 504"
        ]
    ),
    "canary-500-cascade": IncidentAlert(
        id="INC-2026-003",
        title="Regresion tras despliegue Canary: Errores HTTP 500 en Checkout",
        severity="P1-Critica",
        service="checkout-frontend-api",
        environment="production",
        source="Datadog APM",
        summary="Aumento abrupto en la tasa de errores HTTP 500 (15%) inmediatamente posterior a la activacion del canary v2.14.0.",
        metrics={
            "http_500_percentage": "15.8%",
            "canary_traffic_weight": "20%",
            "stable_traffic_weight": "80%",
            "error_distribution": "99.2% de los errores provienen de pods con version v2.14.0"
        },
        logs=[
            "2026-09-10T20:25:01Z level=error msg='TypeError: Cannot read property idempotencyKey of undefined' version=v2.14.0",
            "2026-09-10T20:25:05Z level=error msg='Unhandled promise rejection in route /v1/checkout/process' version=v2.14.0",
            "2026-09-10T20:25:08Z level=info msg='HTTP 200 OK duration=35ms' version=v2.13.8"
        ],
        k8s_events=[
            "Normal Pulled 10m ago kubelet: Successfully pulled image 'registry.company.com/checkout:v2.14.0'",
            "Normal Created 10m ago kubelet: Created container checkout-canary"
        ]
    )
}
