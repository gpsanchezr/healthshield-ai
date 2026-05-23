"""
Views del Dashboard — agrega datos para las gráficas Chart.js + render HTML.
"""
from collections import defaultdict

from django.db.models import Avg, Count
from django.http import HttpResponse
from django.template.loader import get_template
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.authentication.permissions import EsMedico
from apps.etl.models import Paciente, RegistroClinico, EjecucionETL
from apps.ml.models import ModeloML
from apps.analytics.models import Alerta






def dashboard_home_view(request):
    """Renderiza el template: frontend/templates/dashboard/index.html"""
    template = get_template("dashboard/index.html")
    return HttpResponse(template.render({}, request))



class DashboardSummaryView(APIView):
    """
    GET /api/dashboard/
    Panel principal — datos para todas las gráficas Chart.js.
    """
    permission_classes = [IsAuthenticated, EsMedico]

    @extend_schema(summary="Panel del Dashboard")
    def get(self, request):
        # Distribución de riesgo (donut)
        riesgo_qs = (
            RegistroClinico.objects
            .values('riesgo_enfermedad')
            .annotate(count=Count('id'))
        )
        riesgo_labels = []
        riesgo_data = []
        for item in riesgo_qs:
            riesgo_labels.append(item['riesgo_enfermedad'] or 'Sin dato')
            riesgo_data.append(item['count'])

        # Top diagnósticos (barras horizontales)
        diagnosticos_qs = (
            RegistroClinico.objects
            .exclude(diagnostico_preliminar__isnull=True)
            .exclude(diagnostico_preliminar='')
            .values('diagnostico_preliminar')
            .annotate(count=Count('id'))
            .order_by('-count')[:8]
        )
        diag_labels = [d['diagnostico_preliminar'] for d in diagnosticos_qs]
        diag_data = [d['count'] for d in diagnosticos_qs]

        # IMC promedio por grupo etario (línea)
        imc_por_edad = self._imc_por_grupo_etario()

        # Glucosa vs Presión sistólica (scatter)
        scatter_data = self._glucosa_vs_presion()

        # ETL: tendencia de riesgo en últimas ejecuciones
        etl_tendencia = self._etl_tendencia()

        # Modelo activo
        modelo = ModeloML.objects.filter(activo=True).order_by('-entrenado_en').first()

        # KPIs adicionales (promedios de signos vitales)
        vital_stats = RegistroClinico.objects.aggregate(
            imc_avg=Avg('imc'),
            gluc_avg=Avg('glucosa'),
            ps_avg=Avg('presion_sistolica'),
        )
        last_etl = (
            EjecucionETL.objects.filter(estado='completado')
            .order_by('-fecha_inicio')
            .values('fecha_inicio', 'registros_procesados', 'quality_score')
            .first()
        )
        ultima_etl_str = (
            f"{last_etl['fecha_inicio']} - "
            f"{last_etl['registros_procesados']} regs - "
            f"Q={last_etl['quality_score']}"
            if last_etl else None
        )

        return Response({
            'kpi_resumen': {
                'total_pacientes': Paciente.objects.count(),
                'total_registros': RegistroClinico.objects.count(),
                'modelo_activo': modelo.nombre if modelo else None,
                'modelo_accuracy': modelo.accuracy if modelo else None,
                'promedio_imc': round(float(vital_stats['imc_avg'] or 0), 2),
                'promedio_glucosa': round(float(vital_stats['gluc_avg'] or 0), 2),
                'promedio_presion_sistolica': round(float(vital_stats['ps_avg'] or 0), 2),
                'ultima_ejecucion_etl': ultima_etl_str,
                'alertas_activas': Alerta.objects.filter(fecha_vista__isnull=True).count(),
            },
            'grafica_riesgo': {
                'labels': riesgo_labels,
                'data': riesgo_data,
            },
            'grafica_diagnosticos': {
                'labels': diag_labels,
                'data': diag_data,
            },
            'grafica_imc_edad': imc_por_edad,
            'grafica_glucosa_presion': scatter_data,
            'grafica_etl_tendencia': etl_tendencia,
        })

    def _imc_por_grupo_etario(self) -> dict:
        """Agrupa pacientes en grupos etarios de 5 años y calcula IMC promedio."""
        pacientes = Paciente.objects.values('edad', 'registros__imc')

        grupos = defaultdict(list)
        for p in pacientes:
            if p['edad'] and p['registros__imc']:
                grupo = (p['edad'] // 5) * 5
                grupos[grupo].append(float(p['registros__imc']))

        labels = sorted(grupos.keys())
        data = [round(sum(grupos[label]) / len(grupos[label]), 2) for label in labels]

        return {
            'labels': [f"{label}-{label+4}" for label in labels],
            'data': data,
        }

    def _glucosa_vs_presion(self) -> dict:
        """Datos scatter: glucosa vs presión sistólica por paciente."""
        registros = (
            RegistroClinico.objects
            .select_related('paciente')
            .exclude(glucosa__isnull=True)
            .exclude(presion_sistolica__isnull=True)
            .values('glucosa', 'presion_sistolica')[:500]
        )
        data = [
            {'x': float(r['glucosa']), 'y': float(r['presion_sistolica'])}
            for r in registros
        ]
        return {'datasets': [{'label': 'Pacientes', 'data': data}]}

    def _etl_tendencia(self) -> dict:
        """Últimas 10 ejecuciones ETL con calidad score."""
        ejecuciones = (
            EjecucionETL.objects
            .filter(estado='completado')
            .order_by('-fecha_inicio')[:10]
            .values('fecha_inicio', 'registros_procesados', 'quality_score')
        )
        labels = []
        data = []
        for e in reversed(list(ejecuciones)):
            labels.append(e['fecha_inicio'].strftime('%d/%m %H:%M'))
            data.append(e['quality_score'] or 0)

        return {
            'labels': labels,
            'datasets': [{
                'label': 'Quality Score',
                'data': data,
            }],
        }