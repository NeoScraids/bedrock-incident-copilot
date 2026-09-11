"""
Agente autonomo de triaje y respuesta a incidentes utilizando LiteLLM y Amazon Bedrock.
"""

import json
from typing import Dict, Any
from src.config import settings
from src.models import IncidentAlert, IncidentDiagnosis, RemediationStep


SYSTEM_PROMPT = """Eres un Ingeniero Principal de SRE (Site Reliability Engineering) y DevOps.
Tu objetivo es analizar telemetria, logs de error, eventos de Kubernetes y metricas para:
1. Determinar el impacto real y el radio de explosion (blast radius).
2. Aislar la causa raiz tecnica del incidente (RCA).
3. Formular un plan de accion inmediato con comandos especificos ejecutables (kubectl, curl, bash).
4. Proponer medidas preventivas y post-mortem.

Debes responder estrictamente en formato JSON con la siguiente estructura:
{
  "incident_id": "ID del incidente",
  "service": "Servicio afectado",
  "evaluated_severity": "P1-Critica | P2-Alta | P3-Media | P4-Baja",
  "blast_radius": "Descripcion del alcance e impacto en usuarios",
  "root_cause_analysis": "Explicacion tecnica y detallada de la causa raiz",
  "immediate_actions": [
    {
      "order": 1,
      "action": "Descripcion de la accion inmediata",
      "command": "Comando exacto a ejecutar",
      "expected_outcome": "Resultado esperado tras la ejecucion"
    }
  ],
  "preventative_measures": [
    "Recomendacion 1",
    "Recomendacion 2"
  ],
  "confidence_score": 0.95
}
"""


def _generate_mock_diagnosis(alert: IncidentAlert) -> IncidentDiagnosis:
    """
    Genera un diagnostico SRE realista para ejecuciones desatendidas o demos locales.
    """
    if "oom-killed" in alert.id.lower() or "oom" in alert.title.lower():
        return IncidentDiagnosis(
            incident_id=alert.id,
            service=alert.service,
            evaluated_severity="P1-Critica",
            blast_radius="Procesamiento de pagos por lotes degradado. 128 transacciones fallidas por segundo y reinicio ciclico de pods.",
            root_cause_analysis=(
                "El microservicio payments-processor sufrio un desbordamiento de memoria heap (java.lang.OutOfMemoryError) "
                "durante la ingesta de cargas de 4.2MB, excediendo el limite estricto de contenedor fijado en 512Mi. "
                "El kernel de Linux envio la senal SIGKILL (Exit code 137) provocando CrashLoopBackOff."
            ),
            immediate_actions=[
                RemediationStep(
                    order=1,
                    action="Aumentar temporalmente el limite de memoria del pod a 1024Mi para mitigar la cascada de reinicios",
                    command="kubectl patch deployment payments-processor -n production --patch '{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"payments-processor\",\"resources\":{\"limits\":{\"memory\":\"1024Mi\"},\"requests\":{\"memory\":\"512Mi\"}}}]}}}}'",
                    expected_outcome="Los nuevos pods alcanzan estado Running (1/1) sin terminaciones OOMKilled."
                ),
                RemediationStep(
                    order=2,
                    action="Reiniciar progresivamente el despliegue para limpiar contenedores bloqueados",
                    command="kubectl rollout restart deployment/payments-processor -n production",
                    expected_outcome="Rollout progresivo sin tiempo de inactividad completado."
                ),
                RemediationStep(
                    order=3,
                    action="Monitorizar tasa de transacciones fallidas en Prometheus",
                    command="curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(failed_transactions_total[2m]))'",
                    expected_outcome="La metrica cae por debajo de 0.1 transacciones/segundo."
                )
            ],
            preventative_measures=[
                "Implementar paginacion y streaming en la ingestion de pagos para limitar tamano maximo de payloads a 500KB.",
                "Configurar Horizontal Pod Autoscaler (HPA) con metrica de utilizacion de memoria al 75%.",
                "Establecer alertas tempranas de Prometheus con umbral al 85% del memory limit."
            ],
            confidence_score=0.98
        )
    elif "db-connection-pool" in alert.id.lower() or "pool" in alert.title.lower():
        return IncidentDiagnosis(
            incident_id=alert.id,
            service=alert.service,
            evaluated_severity="P2-Alta",
            blast_radius="Latencia P99 degradada a 4.8s. 8.4% de los inicios de sesion experimentan timeouts HTTP 504.",
            root_cause_analysis=(
                "Saturacion del pool de conexiones HikariCP (100/100 activas). El escalado horizontal de réplicas de 3 a 6 pods "
                "multiplico la contencion sobre PostgreSQL sin incrementar los limites de max_connections en la base de datos."
            ),
            immediate_actions=[
                RemediationStep(
                    order=1,
                    action="Reducir las réplicas del deployment para aliviar la contencion de conexiones en el cluster de base de datos",
                    command="kubectl scale deployment/auth-service -n production --replicas=3",
                    expected_outcome="Disminuye la saturacion de conexiones activas en PostgreSQL."
                ),
                RemediationStep(
                    order=2,
                    action="Verificar conexiones activas y consultas bloqueantes en PostgreSQL",
                    command="kubectl exec -it postgres-primary-0 -n database -- psql -U postgres -c 'SELECT pid, state, wait_event, query FROM pg_stat_activity WHERE state != \"idle\";'",
                    expected_outcome="Identificacion de transacciones de larga duracion."
                )
            ],
            preventative_measures=[
                "Desplegar PgBouncer como middleware de agrupamiento de conexiones transaccionales.",
                "Reducir maximumPoolSize por replica en la configuracion de HikariCP a un valor proporcional al total de pods permitidos."
            ],
            confidence_score=0.94
        )
    else:
        return IncidentDiagnosis(
            incident_id=alert.id,
            service=alert.service,
            evaluated_severity="P1-Critica",
            blast_radius="15.8% de las peticiones de checkout fallando con HTTP 500 debido al release canary v2.14.0.",
            root_cause_analysis=(
                "Excepcion no controlada 'TypeError: Cannot read property idempotencyKey of undefined' "
                "introducida en el commit reciente del release canary v2.14.0. El 99.2% de los fallos se originan en este subset."
            ),
            immediate_actions=[
                RemediationStep(
                    order=1,
                    action="Drenar y anular inmediatamente el peso de trafico hacia la version canary mediante Istio / VirtualService",
                    command="kubectl patch virtualservice checkout-route -n production --type='json' -p='[{\"op\":\"replace\",\"path\":\"/spec/http/0/route/1/weight\",\"value\":0},{\"op\":\"replace\",\"path\":\"/spec/http/0/route/0/weight\",\"value\":100}]'",
                    expected_outcome="El 100% del trafico es servido por la version estable v2.13.8. La tasa de error 500 cae a 0%."
                ),
                RemediationStep(
                    order=2,
                    action="Eliminar los pods de la version defectuosa",
                    command="kubectl delete deployment checkout-canary -n production",
                    expected_outcome="Cese total de la ejecucion del artefacto regresivo."
                )
            ],
            preventative_measures=[
                "Configurar automated canary rollback con Argo Rollouts basado en la tasa de errores de Grafana.",
                "Agregar pruebas de integracion end-to-end obligatorias en la pipeline de CI para verificar campos de idempotencia."
            ],
            confidence_score=0.99
        )


def analyze_incident(alert: IncidentAlert) -> IncidentDiagnosis:
    """
    Ejecuta el analisis del incidente mediante LiteLLM + Bedrock, o fallback en modo mock.
    """
    if settings.is_mock:
        return _generate_mock_diagnosis(alert)

    try:
        import litellm

        user_content = (
            f"Analiza la siguiente alerta de incidente:\n"
            f"- ID: {alert.id}\n"
            f"- Titulo: {alert.title}\n"
            f"- Servicio: {alert.service}\n"
            f"- Entorno: {alert.environment}\n"
            f"- Origen: {alert.source}\n"
            f"- Resumen: {alert.summary}\n"
            f"- Metricas: {json.dumps(alert.metrics, ensure_ascii=False)}\n"
            f"- Logs recientes: {json.dumps(alert.logs, ensure_ascii=False)}\n"
            f"- Eventos K8s: {json.dumps(alert.k8s_events, ensure_ascii=False)}\n"
        )

        response = litellm.completion(
            model=settings.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            response_format={"type": "json_object"}
        )

        raw_output = response.choices[0].message.content
        parsed = json.loads(raw_output)
        return IncidentDiagnosis(**parsed)

    except Exception as e:
        print(f"[Advertencia] Error al invocar LiteLLM/Bedrock ({settings.model}): {str(e)}. Utilizando fallback local.")
        return _generate_mock_diagnosis(alert)
