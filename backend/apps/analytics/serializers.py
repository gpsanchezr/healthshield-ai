from rest_framework import serializers

from .models import Alerta


class AlertaSerializer(serializers.ModelSerializer):
    paciente_id = serializers.IntegerField(source='paciente.id', read_only=True)
    paciente_nombre = serializers.SerializerMethodField()
    visto_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Alerta
        fields = [
            'id', 'paciente_id', 'paciente_nombre', 'tipo_alerta',
            'descripcion', 'nivel_urgencia', 'fecha_alerta',
            'fecha_vista', 'visto_por', 'visto_por_nombre',
        ]

    def get_paciente_nombre(self, obj):
        return str(obj.paciente)

    def get_visto_por_nombre(self, obj):
        return str(obj.visto_por) if obj.visto_por else None


class KPICalculatorResultSerializer(serializers.Serializer):
    total_pacientes = serializers.IntegerField()
    total_registros = serializers.IntegerField()
    promedio_edad = serializers.FloatField()
    pacientes_por_riesgo = serializers.DictField(child=serializers.IntegerField())
    imc_promedio = serializers.FloatField()
    glucosa_promedio = serializers.FloatField()
    presion_sistolica_promedio = serializers.FloatField()
    alertas_activas = serializers.IntegerField()
    ultima_ejecucion_etl = serializers.CharField(allow_null=True)