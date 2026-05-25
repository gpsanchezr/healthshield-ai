from typing import Any, cast
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.authentication.permissions import EsMedico
from apps.etl.models import Paciente, RegistroClinico

from .models import ModeloML, Prediccion
from .predictor import ModelPredictor
from .serializers import (
    PrediccionSerializer,
    ModeloMLSerializer,
)

Paciente = cast(Any, Paciente)
RegistroClinico = cast(Any, RegistroClinico)
ModeloML = cast(Any, ModeloML)
Prediccion = cast(Any, Prediccion)


class PredecirRiesgoView(APIView):
    """
    POST /api/ml/predict/paciente/{paciente_id}/
    Ejecuta predicción ML + XAI para un paciente específico.
    Roles: Médico, Administrador.
    """
    permission_classes = [IsAuthenticated, EsMedico]

    @extend_schema(
        summary="Predecir riesgo de paciente",
        description="Ejecuta el modelo Random Forest sobre los datos clínicos del paciente y retorna explicaciones XAI.",
        responses={200: PrediccionSerializer},
    )
    def post(self, _request, paciente_id):
        try:
            paciente = Paciente.objects.get(id=paciente_id)  # type: ignore[attr-defined]
        except Paciente.DoesNotExist:  # type: ignore[attr-defined]
            return Response(
                {'error': 'Paciente no encontrado'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Obtener último registro clínico
        registro = RegistroClinico.objects.filter(paciente=paciente).order_by('-fecha_consulta').first()  # type: ignore[attr-defined]
        if not registro:
            return Response(
                {'error': 'El paciente no tiene registros clínicos'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Preparar datos del registro (solo campos del modelo RegistroClinico)
        imc = None
        if registro.peso and registro.altura and registro.altura > 0:
            imc = round(registro.peso / (registro.altura ** 2), 2)

        registro_data = {
            'imc': imc,
            'presion_sistolica': registro.presion_sistolica,
            'presion_diastolica': registro.presion_diastolica,
            'frecuencia_cardiaca': registro.frecuencia_cardiaca,
            'glucosa': float(registro.glucosa) if registro.glucosa else None,
            'peso': float(registro.peso) if registro.peso else None,
            'altura': float(registro.altura) if registro.altura else None,
            'edad': paciente.edad,
        }

        # Obtener modelo activo de manera segura
        modelo_activo = ModeloML.objects.filter(activo=True).order_by('-entrenado_en').first()  # type: ignore[attr-defined]
        if not modelo_activo or not modelo_activo.archivo_modelo:
            return Response(
                {'error': 'No hay un modelo de Machine Learning activo o configurado.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Ejecutar predictor (ModelPredictor ya carga el modelo activo internamente)
        predictor = ModelPredictor()
        result = predictor.predict(registro_data)

        # Guardar predicción en BD
        prediccion = Prediccion.objects.create(  # type: ignore[attr-defined]
            paciente=paciente,
            modelo=modelo_activo,
            riesgo_predicho=result['riesgo_predicho'],
            probabilidad=result['probabilidades'].get(result['riesgo_predicho'], 0.0),
            factores_clave=result['factores_clave'],
        )

        return Response({
            'prediccion': PrediccionSerializer(prediccion).data,
            'paciente_id': paciente_id,
            'modelo': modelo_activo.nombre if modelo_activo else None,
        })


class ModeloMetricsView(APIView):
    """
    GET /api/ml/modelos/
    Lista todos los modelos ML con sus métricas.
    Roles: Médico, Administrador.
    """
    permission_classes = [IsAuthenticated, EsMedico]

    @extend_schema(
        summary="Listar modelos ML",
        description="Retorna todos los modelos entrenados con métricas.",
        responses={200: ModeloMLSerializer(many=True)},
    )
    def get(self, _request):
        modelos = ModeloML.objects.order_by('-entrenado_en')[:10]  # type: ignore[attr-defined]
        serializer = ModeloMLSerializer(modelos, many=True)
        return Response({'modelos': serializer.data})


class ModeloActivoMetricsView(APIView):
    """
    GET /api/ml/metrics/
    Retorna métricas del modelo activo.
    Roles: Público autenticado.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Métricas del modelo activo",
        description="Retorna accuracy, precision, recall, f1 del modelo actualmente activo.",
    )
    def get(self, _request):
        modelo = ModeloML.objects.filter(activo=True).order_by('-entrenado_en').first()  # type: ignore[attr-defined]
        if not modelo:
            return Response({'error': 'No hay modelo activo'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'nombre': modelo.nombre,
            'algoritmo': modelo.algoritmo,
            'version': modelo.version,
            'accuracy': modelo.accuracy,
            'precision_score': modelo.precision_score,
            'recall': modelo.recall,
            'f1_score': modelo.f1_score,
            'feature_importance': modelo.feature_importance,
            'entrenado_en': modelo.entrenado_en,
        })


class PredecirSignosView(APIView):
    """
    POST /api/ml/predict/signos/
    Recibe signos vitales en JSON directamente y retorna predicción de riesgo.

    Ejemplo de request body:
    {
        "edad": 45,
        "imc": 28.5,
        "presion_sistolica": 135,
        "presion_diastolica": 88,
        "frecuencia_cardiaca": 75,
        "glucosa": 110,
        "colesterol": 200,
        "saturacion_oxigeno": 98,
        "temperatura": 36.8,
        "fumador": false,
        "consumo_alcohol": false,
        "antecedentes_familiares": true
    }

    No requiere paciente_id — funciona con datos crudos en tiempo real.
    """
    permission_classes = [IsAuthenticated, EsMedico]

    @extend_schema(
        summary="Predecir riesgo desde signos vitales",
        description="Recibe un JSON con signos vitales y retorna probabilidad de riesgo (RandomForest + XAI).",
        tags=['ML'],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'edad': {'type': 'number', 'description': 'Años'},
                    'imc': {'type': 'number', 'description': 'Índice de masa corporal'},
                    'presion_sistolica': {'type': 'number', 'description': 'mmHg'},
                    'presion_diastolica': {'type': 'number', 'description': 'mmHg'},
                    'frecuencia_cardiaca': {'type': 'number', 'description': 'lpm'},
                    'glucosa': {'type': 'number', 'description': 'mg/dL'},
                    'colesterol': {'type': 'number', 'description': 'mg/dL'},
                    'saturacion_oxigeno': {'type': 'number', 'description': '%'},
                    'temperatura': {'type': 'number', 'description': '°C'},
                    'fumador': {'type': 'boolean'},
                    'consumo_alcohol': {'type': 'boolean'},
                    'antecedentes_familiares': {'type': 'boolean'},
                },
                'required': ['edad', 'presion_sistolica', 'presion_diastolica', 'glucosa'],
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'riesgo_predicho': {'type': 'string', 'example': 'Medio'},
                    'probabilidades': {
                        'type': 'object',
                        'example': {'Bajo': 0.45, 'Medio': 0.38, 'Alto': 0.14, 'Crítico': 0.03},
                    },
                    'factores_clave': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'variable': {'type': 'string'},
                                'impacto': {'type': 'number'},
                                'direccion': {'type': 'string'},
                            },
                        },
                    },
                },
            },
        },
    )
    def post(self, request):
        signos = request.data
        required = ['edad', 'presion_sistolica', 'presion_diastolica', 'glucosa']
        missing = [f for f in required if f not in signos]
        if missing:
            return Response(
                {'error': f'Campos requeridos faltantes: {missing}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        modelo_activo = ModeloML.objects.filter(activo=True).order_by('-entrenado_en').first()  # type: ignore[attr-defined]
        if not modelo_activo or not modelo_activo.archivo_modelo:
            return Response(
                {'error': 'No hay un modelo de Machine Learning activo.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        predictor = ModelPredictor()
        result = predictor.predict(signos)
        return Response(result, status=status.HTTP_200_OK)
