import logging
import pandas as pd
from dataclasses import dataclass

from typing import Dict, Optional


from django.db.models import Avg, Count, FloatField, Q
from django.db.models.functions import Coalesce
from apps.etl.models import Paciente, RegistroClinico, EjecucionETL

logger = logging.getLogger('analytics')


@dataclass
class HealthMetrics:
    """Contenedor de métricas calculado."""

    total_pacientes: int = 0
    total_registros: int = 0
    promedio_edad: float = 0.0
    pacientes_por_riesgo: Optional[Dict[str, int]] = None
    imc_promedio: float = 0.0
    glucosa_promedio: float = 0.0
    presion_sistolica_promedio: float = 0.0
    alertas_activas: int = 0
    ultima_ejecucion_etl: Optional[str] = None
    estadisticas_descriptivas: Optional[Dict[str, dict]] = None

    def __post_init__(self):
        if self.pacientes_por_riesgo is None:
            self.pacientes_por_riesgo = {}
        if self.estadisticas_descriptivas is None:
            self.estadisticas_descriptivas = {}

class KPICalculator:
    """Calcula los 6 KPIs clínicos principales."""
    def calculate(self) -> HealthMetrics:
        logger.info("[KPICalculator] Calculando métricas...")
        
        # Métricas básicas
        total_pacientes = Paciente.objects.count()
        total_registros = RegistroClinico.objects.count()
        
        avg_edad = Paciente.objects.aggregate(
            prom=Coalesce(Avg('edad'), 0.0, output_field=FloatField())
        )['prom']
        
        riesgo_counts = RegistroClinico.objects.values('riesgo_enfermedad').annotate(count=Count('id')).order_by()
        riesgo_dict = {r['riesgo_enfermedad'] or 'Sin dato': r['count'] for r in riesgo_counts}
        
        vital_stats = RegistroClinico.objects.aggregate(
            imc_prom=Coalesce(Avg('imc'), 0.0, output_field=FloatField()),
            gluc_prom=Coalesce(Avg('glucosa'), 0.0, output_field=FloatField()),
            ps_prom=Coalesce(Avg('presion_sistolica'), 0.0, output_field=FloatField()),
        )
        
        # Estadística Descriptiva (Promedio, Std, Moda) usando Pandas para robustez
        estadisticas = {}
        qs_pac = Paciente.objects.values('edad')
        if qs_pac.exists():
            df_pac = pd.DataFrame.from_records(qs_pac)
            estadisticas['edad'] = {
                'promedio': round(float(df_pac['edad'].mean()), 2),
                'std': round(float(df_pac['edad'].std()), 2) if len(df_pac) > 1 else 0.0,
                'moda': round(float(df_pac['edad'].mode()[0]), 2) if not df_pac['edad'].mode().empty else 0.0
            }
            
        qs_reg = RegistroClinico.objects.values('imc', 'glucosa', 'presion_sistolica')
        if qs_reg.exists():
            df_reg = pd.DataFrame.from_records(qs_reg)
            for col in ['imc', 'glucosa', 'presion_sistolica']:
                df_reg[col] = pd.to_numeric(df_reg[col], errors='coerce')
                valid_s = df_reg[col].dropna()
                if not valid_s.empty:
                    estadisticas[col] = {
                        'promedio': round(float(valid_s.mean()), 2),
                        'std': round(float(valid_s.std()), 2) if len(valid_s) > 1 else 0.0,
                        'moda': round(float(valid_s.mode()[0]), 2) if not valid_s.mode().empty else 0.0
                    }
        
        # Alertas activas
        alertas_activas = 0
        try:
            from apps.analytics.models import Alerta
            alertas_activas = Alerta.objects.filter(fecha_vista__isnull=True).count()
        except Exception:
            pass
            
        # Última ejecución ETL
        last_etl = EjecucionETL.objects.filter(estado='completado').order_by('-fecha_inicio').first()
        quality = last_etl.reporte_calidad.get('quality_score') if last_etl and last_etl.reporte_calidad else 'N/A'
        ultima_ejecucion = f"{last_etl.fecha_inicio.strftime('%Y-%m-%d %H:%M')} - Q={quality}" if last_etl else None

        return HealthMetrics(
            total_pacientes=total_pacientes,
            total_registros=total_registros,
            promedio_edad=round(float(avg_edad), 2),
            pacientes_por_riesgo=riesgo_dict,
            imc_promedio=round(float(vital_stats['imc_prom']), 2),
            glucosa_promedio=round(float(vital_stats['gluc_prom']), 2),
            presion_sistolica_promedio=round(float(vital_stats['ps_prom']), 2),
            alertas_activas=alertas_activas,
            ultima_ejecucion_etl=ultima_ejecucion,
            estadisticas_descriptivas=estadisticas
        )


class PacienteCriticoDetector:
    """Detecta pacientes en estado crítico aplicando reglas clínicas."""

    GLUCOSA_CRITICA = 300
    PRESION_SISTOLICA_CRITICA = 180
    SATURACION_CRITICA = 85
    EDAD_CON_RIESGO = 70

    def detect_and_alert(self) -> int:
        """Itera registros clínicos, detecta críticos y crea alertas. Retorna count."""
        from apps.analytics.models import Alerta

        alertas_creadas = 0

        criticos = RegistroClinico.objects.filter(
            Q(glucosa__gt=self.GLUCOSA_CRITICA)
            | Q(presion_sistolica__gt=self.PRESION_SISTOLICA_CRITICA)
            | Q(saturacion_oxigeno__lt=self.SATURACION_CRITICA)
            | Q(riesgo_enfermedad__in=['Alto', 'Crítico'])
        ).select_related('paciente')

        for registro in criticos:
            ya_existe = Alerta.objects.filter(
                paciente=registro.paciente,
                fecha_vista__isnull=True,
                nivel_urgencia__in=['alta', 'critica'],
            ).exists()

            if ya_existe:
                continue

            nivel = 'critica' if registro.riesgo_enfermedad == 'Crítico' else 'alta'
            Alerta.objects.create(
                paciente=registro.paciente,
                tipo_alerta='Paciente crítico detectado',
                descripcion=self._build_description(registro),
                nivel_urgencia=nivel,
            )
            alertas_creadas += 1
            logger.info(f"[Alerta] Paciente {registro.paciente_id} -> {nivel}")

        return alertas_creadas

    def _build_description(self, registro: RegistroClinico) -> str:
        parts = []
        if registro.glucosa and registro.glucosa > self.GLUCOSA_CRITICA:
            parts.append(f"Glucosa elevada: {registro.glucosa} mg/dL")
        if registro.presion_sistolica and registro.presion_sistolica > self.PRESION_SISTOLICA_CRITICA:
            parts.append(f"Presión sistólica alta: {registro.presion_sistolica} mmHg")
        if registro.saturacion_oxigeno and registro.saturacion_oxigeno < self.SATURACION_CRITICA:
            parts.append(f"Saturación de oxígeno baja: {registro.saturacion_oxigeno}%")
        if registro.riesgo_enfermedad in ['Alto', 'Crítico'] and parts:
            parts.append(f"Riesgo algorítmico: {registro.riesgo_enfermedad}")
        if not parts:
            return "Paciente requiere atención inmediata"
        return " | ".join(parts)
