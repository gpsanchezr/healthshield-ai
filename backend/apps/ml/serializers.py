from rest_framework import serializers

from .models import ModeloML, Prediccion


class ModeloMLSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeloML
        fields = [
            'id', 'nombre', 'algoritmo', 'version',
            'accuracy', 'precision_score', 'recall', 'f1_score',
            'feature_importance', 'entrenado_en',
            'registros_entrenamiento', 'activo',
        ]


class PrediccionSerializer(serializers.ModelSerializer):
    paciente_id = serializers.IntegerField(source='paciente.id', read_only=True)
    paciente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Prediccion
        fields = [
            'id', 'paciente_id', 'paciente_nombre',
            'riesgo_predicho', 'probabilidad',
            'factores_clave', 'fecha',
        ]

    def get_paciente_nombre(self, obj):
        return str(obj.paciente)


class PrediccionPacienteRequestSerializer(serializers.Serializer):
    paciente_id = serializers.IntegerField()