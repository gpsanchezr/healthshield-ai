from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.authentication.permissions import EsMedico, EsAnalista, EsAdministrador
from apps.etl.models import Paciente, RegistroClinico

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
            Paciente.objects
            .values('edad_group') if False else []  # annotate would go here
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