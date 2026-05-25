# apps/etl/views.py
"""
API endpoints del módulo ETL.
Controladores para ejecutar pipeline, historial, calidad y simulación.
"""
import os
import tempfile
import pandas as pd
from django.db import models
from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema

from apps.authentication.permissions import EsAdministrador, EsAnalista, EsMedico
from .pipeline import ETLPipeline
from .extractors import CSVExtractor, ExcelExtractor
from .simulation import DataSimulator
from .models import EjecucionETL, Paciente, RegistroClinico
from .serializers import PacienteSerializer, PacienteListSerializer, RegistroClinicoSerializer, SimulateETLSerializer


class RunETLView(APIView):
    """
    POST /api/etl/run/
    Ejecuta el pipeline ETL sobre un archivo subido o el dataset base.
    Roles: Analista, Administrador
    """
    permission_classes = [EsAnalista]

    @extend_schema(
        summary="Ejecutar pipeline ETL",
        description="Carga un archivo CSV/Excel y ejecuta el pipeline completo ETL.",
    )
    def post(self, request):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response(
                {'error': 'Se requiere un archivo CSV o Excel.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        _, ext = os.path.splitext(archivo.name)
        ext = ext.lower()
        if ext not in ['.csv', '.xlsx', '.xls']:
            return Response(
                {'error': 'Formato no soportado. Use .csv, .xlsx o .xls'},
                status=status.HTTP_400_BAD_REQUEST
            )

        temp_fd, temp_path = tempfile.mkstemp(suffix=ext)
        try:
            with os.fdopen(temp_fd, 'wb+') as f:
                for chunk in archivo.chunks():
                    f.write(chunk)

            # Validación de formato antes de ejecutar el ETL
            if ext in ['.xlsx', '.xls']:
                ExcelExtractor().extract(temp_path)
            else:
                CSVExtractor().extract(temp_path)

            pipeline = ETLPipeline(usuario=request.user, tipo='manual')
            result = pipeline.run(temp_path)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class SimulateDataView(APIView):
    """
    POST /api/etl/simular/
    Genera registros sintéticos con errores y ejecuta el ETL.
    Rol: Administrador
    """
    permission_classes = [EsAdministrador]

    def post(self, request):
        serializer = SimulateETLSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        count = serializer.validated_data['count']

        simulator = DataSimulator()
        df = simulator.generate(count)

        pipeline = ETLPipeline(usuario=request.user, tipo='simulacion')
        result = pipeline.run_dataframe(df)
        return Response(result, status=status.HTTP_200_OK)


class HistorialETLView(APIView):
    """
    GET /api/etl/historial/
    Lista las últimas 50 ejecuciones del historial ETL.
    """
    permission_classes = [EsAnalista]

    def get(self, request):
        ejecuciones = EjecucionETL.objects.order_by('-fecha_inicio')[:50]
        data = [
            {
                'id':                    e.id,
                'fecha_inicio':          e.fecha_inicio,
                'duracion_segundos':     e.duracion_segundos,
                'registros_extraidos':   e.registros_extraidos,
                'registros_procesados':  e.registros_procesados,
                'registros_rechazados':  e.registros_rechazados,
                'estado':                e.estado,
                'tipo':                  e.tipo,
                'usuario':               str(e.usuario) if e.usuario else 'Sistema',
                'quality_score':         (e.reporte_calidad or {}).get('quality_score'),
            }
            for e in ejecuciones
        ]
        return Response({'historial': data, 'total': len(data)})


class CalidadReporteView(APIView):
    """
    GET /api/etl/calidad/{ejecucion_id}/
    Retorna el Data Quality Report de una ejecución ETL específica.
    """
    permission_classes = [EsAnalista]

    def get(self, request, ejecucion_id):
        try:
            e = EjecucionETL.objects.get(id=ejecucion_id)
            return Response(e.reporte_calidad or {'error': 'Sin reporte disponible'})
        except EjecucionETL.DoesNotExist:
            return Response({'error': 'Ejecución no encontrada'}, status=status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────────────────────────────────────────
# ViewSets automáticos — CRUD de Paciente y RegistroClinico
# ─────────────────────────────────────────────────────────────────────────────

from rest_framework.permissions import IsAuthenticated


class RegistroClinicoViewSet(viewsets.ModelViewSet):
    """
    API CRUD para Registros Clínicos.

    Endpoints:
      GET    /api/etl/registros/              → lista todos
      POST   /api/etl/registros/              → crear uno
      GET    /api/etl/registros/{id}/         → detalle
      PUT    /api/etl/registros/{id}/         → actualizar
      DELETE /api/etl/registros/{id}/         → eliminar
    """
    queryset = RegistroClinico.objects.select_related('paciente').all()
    serializer_class = RegistroClinicoSerializer
    permission_classes = [IsAuthenticated]


# ─────────────────────────────────────────────────────────────────────────────
# ViewSet para Paciente — CRUD + búsqueda + estadísticas
# ─────────────────────────────────────────────────────────────────────────────

class PacientePagination(PageNumberPagination):
    """Paginación personalizada: 10 pacientes por página."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PacienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Pacientes y sus registros clínicos.

    Endpoints:
      GET    /api/pacientes/             → lista paginada
      POST   /api/pacientes/             → crear paciente
      GET    /api/pacientes/{id}/       → detalle con historial
      PUT    /api/pacientes/{id}/       → actualizar
      DELETE /api/pacientes/{id}/       → eliminar
      GET    /api/pacientes/buscar/?q=  → búsqueda por nombre/apellido
      GET    /api/pacientes/{id}/registros/  → historial clínico del paciente
      GET    /api/pacientes/estadisticas/    → KPIs generales
    """
    queryset = Paciente.objects.prefetch_related('registros').all()
    permission_classes = [EsMedico]  # cualquier rol authenticated
    pagination_class = PacientePagination

    def get_serializer_class(self):
        if self.action == 'list':
            return PacienteListSerializer
        return PacienteSerializer

    @extend_schema(
        summary="Listar pacientes",
        description="Devuelve lista de pacientes con paginación personalizada (10 por página).",
        tags=['Paciente'],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Buscar pacientes",
        description="Búsqueda por nombre o apellido. Filtra sin paginar.",
        tags=['Paciente'],
    )
    @action(detail=False, methods=['get'])
    def buscar(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response({'error': 'Parámetro "q" requerido'}, status=status.HTTP_400_BAD_REQUEST)

        qs = Paciente.objects.filter(
            models.Q(nombres__icontains=q) | models.Q(apellidos__icontains=q)
        )[:50]
        serializer = PacienteListSerializer(qs, many=True)
        return Response({'resultados': serializer.data, 'total': len(serializer.data)})

    @extend_schema(
        summary="Registros clínicos de un paciente",
        description="Devuelve todos los registros clínicos del paciente ordenados por fecha.",
        tags=['Paciente'],
    )
    @action(detail=True, methods=['get'])
    def registros(self, request, pk=None):
        paciente = self.get_object()
        regs = paciente.registros.all().order_by('-fecha_consulta')
        serializer = RegistroClinicoSerializer(regs, many=True)
        return Response({
            'paciente': str(paciente),
            'total': regs.count(),
            'registros': serializer.data,
        })

    @extend_schema(
        summary="Estadísticas generales",
        description="KPIs: total pacientes, distribución por género, rangos etarios, distribución de riesgo.",
        tags=['Paciente'],
    )
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        total = Paciente.objects.count()
        por_sexo = list(Paciente.objects.values('sexo').annotate(c=Count('sexo')))

        menores = Paciente.objects.filter(edad__lt=18).count()
        jovenes = Paciente.objects.filter(edad__gte=18, edad__lte=35).count()
        adultos = Paciente.objects.filter(edad__gte=36, edad__lte=60).count()
        mayores = Paciente.objects.filter(edad__gt=60).count()

        por_riesgo = list(RegistroClinico.objects.values('riesgo_enfermedad').annotate(
            total=Count('riesgo_enfermedad')
        ))
        return Response({
            'total_pacientes': total,
            'por_sexo': por_sexo,
            'rango_etario': {
                'menores': menores,
                'jovenes': jovenes,
                'adultos': adultos,
                'mayores': mayores,
            },
            'por_riesgo': por_riesgo,
        })
