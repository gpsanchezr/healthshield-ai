from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class HealthMetrics:
    total_pacientes: int = 0
    total_registros: int = 0
    promedio_edad: float = 0.0

    pacientes_por_riesgo: Dict[str, int] = field(default_factory=dict)

    imc_promedio: float = 0.0
    glucosa_promedio: float = 0.0
    presion_sistolica_promedio: float = 0.0

    alertas_activas: int = 0
    ultima_ejecucion_etl: Optional[str] = None

