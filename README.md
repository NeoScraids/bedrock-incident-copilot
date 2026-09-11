# bedrock-incident-copilot

Cuando te llega una alerta de produccion (OOMKilled, pool de conexiones agotado, deployment roto), lo primero que haces es ir a ver metricas, luego logs, luego eventos de K8s, y despues decidir que hacer. Este proyecto automatiza ese flujo inicial usando LiteLLM conectado a Amazon Bedrock (Claude 3.5 Sonnet).

Le pasas el payload de la alerta, el agente lo analiza junto con las metricas y logs asociados, y te devuelve:
- Severidad evaluada (P1-P4)
- Causa raiz probable
- Comandos de kubectl/bash para mitigar
- Recomendaciones post-mortem

## Escenarios incluidos

El repo trae 3 incidentes precargados basados en cosas que pasan en produccion:

| Escenario | Que simula |
| :--- | :--- |
| `oom-killed` | Pod de pagos que revienta por payloads de 4MB que desbordan el limit de 512Mi. 12 reinicios en 15 min. |
| `db-connection-pool` | Auth service escala de 3 a 6 pods y agota las 100 conexiones del pool de PostgreSQL. P99 sube a 4.8s. |
| `canary-500-cascade` | Deploy canary v2.14.0 con un TypeError que causa 15% de errores 500 en checkout. |

## Como ejecutarlo

```bash
git clone https://github.com/NeoScraids/bedrock-incident-copilot.git
cd bedrock-incident-copilot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Simular el incidente de OOMKilled (no necesita credenciales de AWS)
python simulate_incident.py --scenario oom-killed

# Correr los 3 escenarios seguidos
python simulate_incident.py --scenario all
```

Con `BEDROCK_MOCK=true` (default) todo corre local sin tocar AWS. Los diagnosticos mock son deterministicos y estan escritos con el mismo nivel de detalle que generaria el modelo real. Si configuras credenciales de Bedrock, cambia a `BEDROCK_MOCK=false` y usa el LLM de verdad.

## Ejemplo de salida

```
===========================================================================
  ALERTA RECIBIDA: [P1-Critica] INC-2026-001
===========================================================================
Servicio:   payments-processor
Resumen:    La tasa de reinicios supero el umbral critico (12 reinicios en 15 min).

Metricas Clave:
  - memory_usage_bytes: 536870912 / 536870912 (100% del limit 512Mi)
  - failed_transactions_per_second: 128.5

===========================================================================
  DIAGNOSTICO GENERADO
===========================================================================
Severidad:  P1-Critica
Confianza:  98%

Causa Raiz:
  OutOfMemoryError en heap por payloads de 4.2MB. Exit code 137 (SIGKILL).

Mitigacion:
  [1] kubectl patch deployment payments-processor -n production --patch '...'
      -> Subir memory limit a 1024Mi
  [2] kubectl rollout restart deployment/payments-processor -n production
      -> Limpiar pods bloqueados
```

## Estructura

```
src/
  config.py                        # Settings y modo mock/live
  models.py                        # IncidentAlert, IncidentDiagnosis (Pydantic)
  agents/
    incident_agent.py              # Logica del agente (LiteLLM o fallback local)
  scenarios/
    incident_catalogue.py          # Los 3 incidentes precargados
simulate_incident.py               # CLI principal
Dockerfile
```

## Contexto

En el trabajo manejo respuesta a incidentes y queria ver hasta donde podia llegar un agente con LiteLLM haciendo el triage inicial automaticamente. Este repo es esa prueba de concepto limpia, sin datos de la empresa.

## Licencia

MIT
