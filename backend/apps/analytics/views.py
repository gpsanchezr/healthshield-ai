import pandas as pd
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.authentication.permissions import EsMedico, EsAnalista, EsAdministrador
from apps.etl.models import Paciente, RegistroClinico
from django.db.models import Count, Case, When, Value, CharField, F

from .models import Alerta
from .calculators import KPICalculator, PacienteCriticoDetector
from .serializers import AlertaSerializer,KPICalculatorResultSerializer


class DashboardKPIsView(APIView):
    """
    GET /api/analytics/kpis/
    Retorna los 6 KPIs clínicos en tiempo real.
    Roles: Médico, Analista, Administrador.
    """
    permission_classes = [IsAuthenticated, EsMedico]

    @extend_schema(
        summary="KPIs del Dashboard",
        description="Retorna métricas agregadas: total pacientes, distribución de riesgo, promedios de signos vitales.",
        responses={200: KPICalculatorResultSerializer},
    )
    def get(self, request):
        calculator = KPICalculator()
        metrics = calculator.calculate()

        # Serializar dataclass → dict
        data = {
            'total_pacientes': metrics.total_pacientes,
            'total_registros': metrics.total_registros,
            'promedio_edad': metrics.promedio_edad,
            'pacientes_por_riesgo': metrics.pacientes_por_riesgo,
            'imc_promedio': metrics.imc_promedio,
            'glucosa_promedio': metrics.glucosa_promedio,
            'presion_sistolica_promedio': metrics.presion_sistolica_promedio,
            'alertas_activas': metrics.alertas_activas,
            'ultima_ejecucion_etl': metrics.ultima_ejecucion_etl,
            'estadisticas_descriptivas': metrics.estadisticas_descriptivas,
        }
        return Response(data)


class AlertasListView(APIView):
    """
    GET /api/analytics/alertas/
    Lista alertas paginadas con filtros.
    """
    permission_classes = [IsAuthenticated, EsMedico]

    @extend_schema(
        summary="Listar alertas",
        description="Lista alertas con filtro opcional por nivel de urgencia.",
        parameters=[
            OpenApiParameter(name='urgencia', type=str, required=False),
        ],
        responses={200: AlertaSerializer(many=True)},
    )
    def get(self, request):
        urgencia = request.query_params.get('urgencia')
        queryset = Alerta.objects.select_related('paciente', 'visto_por')

        if urgencia:
            queryset = queryset.filter(nivel_urgencia=urgencia)

        queryset = queryset[:50]
        serializer = AlertaSerializer(queryset, many=True)
        return Response({'alertas': serializer.data, 'total': queryset.count()})


class PacientesSegmentacionView(APIView):
    """
    GET /api/analytics/segmentacion/
    Retorna segmentación de pacientes por grupo de riesgo y demografía.
    Roles: Analista, Administrador.
    """
    permission_classes = [IsAuthenticated, EsAnalista]

    @extend_schema(summary="Segmentación de pacientes")
    def get(self, request):
        # Segmentación por rango de edad
        segmentos_edad = (
            Paciente.objects.annotate(
                edad_group=Case(
                    When(edad__lt=18, then=Value('Menores (<18)')),
                    When(edad__range=[18, 35], then=Value('Jóvenes (18-35)')),
                    When(edad__range=[36, 60], then=Value('Adultos (36-60)')),
                    default=Value('Mayores (>60)'),
                    output_field=CharField(),
                )
            ).values('edad_group').annotate(count=Count('id')).order_by('edad_group')
        )

        # Por riesgo
        riesgo_dist = (
            RegistroClinico.objects
            .values('riesgo_enfermedad')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Por clasificación IMC
        imc_dist = (
            RegistroClinico.objects
            .values('clasificacion_imc')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return Response({
            'distribucion_riesgo': {r['riesgo_enfermedad']: r['count'] for r in riesgo_dist},
            'distribucion_imc': {r['clasificacion_imc']: r['count'] for r in imc_dist},
            'distribucion_edad': {r['edad_group']: r['count'] for r in segmentos_edad},
        })


class AlertaMarcarVistaView(APIView):
    """POST /api/analytics/alertas/{id}/ — Marca una alerta como vista."""
    permission_classes = [IsAuthenticated, EsMedico]

    @extend_schema(summary="Marcar alerta como vista")
    def post(self, request, alerta_id):
        try:
            alerta = Alerta.objects.get(id=alerta_id)
        except Alerta.DoesNotExist:
            return Response({'error': 'Alerta no encontrada'}, status=404)

        from django.utils import timezone
        alerta.visto_por = request.user
        alerta.fecha_vista = timezone.now()
        alerta.save(update_fields=['visto_por', 'fecha_vista'])

        return Response({'status': 'marcada_como_vista'})


class DetectarCriticosView(APIView):
    """
    POST /api/analytics/detectar-criticos/
    Ejecuta la detección de pacientes críticos y genera alertas.
    Roles: Analista, Administrador.
    """
    permission_classes = [IsAuthenticated, EsAnalista]

    @extend_schema(summary="Detectar pacientes críticos")
    def post(self, request):
        detector = PacienteCriticoDetector()
        count = detector.detect_and_alert()
        return Response({
            'status': 'completado',
            'alertas_generadas': count,
            'mensaje': f'Se generaron {count} alertas de pacientes críticos.',
        })


class HeatmapCorrelacionView(APIView):
    """
    GET /api/analytics/correlacion/
    Calcula la correlación de Pearson entre variables clínicas para el Heatmap.
    Roles: Analista, Administrador.
    """
    permission_classes = [IsAuthenticated, EsAnalista]

    @extend_schema(summary="Heatmap de Correlación Clínica")
    def get(self, request):
        # Extraer edad del paciente junto con sus signos vitales
        qs = RegistroClinico.objects.annotate(edad=F('paciente__edad')).values(
            'edad', 'imc', 'glucosa', 'presion_sistolica', 'presion_diastolica',
            'frecuencia_cardiaca', 'colesterol', 'saturacion_oxigeno'
        )
        if not qs.exists():
            return Response({"error": "No hay datos suficientes"}, status=404)

        df = pd.DataFrame.from_records(qs)
        df = df.apply(pd.to_numeric, errors='coerce')
        corr_matrix = df.corr(method='pearson').fillna(0).round(2)

        labels = corr_matrix.columns.tolist()
        data = []
        for i, row_label in enumerate(labels):
            for j, col_label in enumerate(labels):
                data.append({
                    'x': col_label,
                    'y': row_label,
                    'v': corr_matrix.iloc[i, j]
                })

        return Response({'labels': labels, 'data': data})