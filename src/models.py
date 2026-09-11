"""
Modelos de datos para incidentes, contexto SRE y reportes de diagnostico.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class IncidentAlert(BaseModel):
    id: str = Field(description="Identificador unico del incidente")
    title: str = Field(description="Titulo de la alerta")
    severity: str = Field(description="Severidad reportada: P1-Critica, P2-Alta, P3-Media, P4-Baja")
    service: str = Field(description="Nombre del microservicio afectado")
    environment: str = Field(description="Entorno (production, staging, dev)")
    source: str = Field(description="Origen de la alerta (Alertmanager, Azure Monitor, Datadog)")
    summary: str = Field(description="Descripcion textual de la alerta")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Metricas asociadas (CPU, RAM, ErrorRate, Latency)")
    logs: List[str] = Field(default_factory=list, description="Ultimas lineas relevantes del log")
    k8s_events: List[str] = Field(default_factory=list, description="Eventos de Kubernetes asociados")


class RemediationStep(BaseModel):
    order: int
    action: str
    command: Optional[str] = None
    expected_outcome: str


class IncidentDiagnosis(BaseModel):
    incident_id: str
    service: str
    evaluated_severity: str
    blast_radius: str = Field(description="Impacto estimado en usuarios o servicios dependientes")
    root_cause_analysis: str = Field(description="Analisis tecnico de la causa raiz")
    immediate_actions: List[RemediationStep] = Field(description="Pasos de mitigacion inmediata")
    preventative_measures: List[str] = Field(description="Recomendaciones post-mortem a mediano plazo")
    confidence_score: float = Field(description="Confianza del agente entre 0.0 y 1.0")
