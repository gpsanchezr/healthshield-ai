from rest_framework import serializers
from drf_spectacular.utils import extend_schema

from .models import Paciente, RegistroClinico


class RegistroClinicoSerializer(serializers.ModelSerializer):
    """Serializer para los registros clínicos de un paciente."""

    class Meta:
        model = RegistroClinico
        fields = [
            'id', 'fecha_consulta',
            'peso', 'altura',
            'presion_sistolica', 'presion_diastolica',
            'glucosa', 'frecuencia_cardiaca',
            'riesgo_enfermedad',
        ]
        read_only_fields = ['id', 'fecha_consulta']


class PacienteSerializer(serializers.ModelSerializer):
    """
    Serializer completo del modelo Paciente.
    Incluye registros clínicos anidados y total_registros.
    """
    registros = RegistroClinicoSerializer(many=True, read_only=True)
    total_registros = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = [
            'id', 'nombres', 'apellidos', 'edad', 'sexo',
            'fecha_registro',
            'total_registros', 'registros',
        ]
        read_only_fields = ['id', 'fecha_registro', 'total_registros']

    @extend_schema(
        description="Cantidad de registros clínicos de este paciente.",
        tags=['Paciente'],
    )
    def get_total_registros(self, obj) -> int:
        return obj.registros.count()


class PacienteListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listado — sin registros anidados."""

    class Meta:
        model = Paciente
        fields = ['id', 'nombres', 'apellidos', 'edad', 'sexo', 'fecha_registro']


# ── Serializers para ETL ──────────────────────────────────────────────────────

class RunETLSerializer(serializers.Serializer):
    archivo = serializers.FileField(required=False)


class SimulateETLSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=1, max_value=500, default=10)