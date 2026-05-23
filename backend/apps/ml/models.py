from django.conf import settings
from django.db import models


class ModeloML(models.Model):
    """Modelo de Machine Learning versionado y evaluado."""

    ALGORITHM_CHOICES = [
        ('random_forest', 'Random Forest'),
        ('logistic_regression', 'Logistic Regression'),
        ('decision_tree', 'Decision Tree'),
    ]

    nombre = models.CharField(max_length=100)
    algoritmo = models.CharField(max_length=50, choices=ALGORITHM_CHOICES)
    version = models.CharField(max_length=20)

    # Métricas de evaluación
    accuracy = models.FloatField(null=True, blank=True)
    precision_score = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)

    # Persistencia
    archivo_modelo = models.CharField(max_length=255, null=True, blank=True)

    # Metadatos
    feature_names = models.JSONField(null=True, blank=True)
    feature_importance = models.JSONField(null=True, blank=True)
    entrenado_en = models.DateTimeField(auto_now_add=True)
    registros_entrenamiento = models.IntegerField(default=0)
    activo = models.BooleanField(default=False)

    class Meta:
        ordering = ['-entrenado_en']

    def __str__(self):
        return f"{self.nombre} {self.version} (acc={self.accuracy})"


class Prediccion(models.Model):
    """Predicción individual generada por el motor ML."""

    paciente = models.ForeignKey(
        'etl.Paciente',
        on_delete=models.CASCADE,
        related_name='predicciones',
    )
    modelo = models.ForeignKey(
        ModeloML,
        on_delete=models.SET_NULL,
        null=True,
        related_name='predicciones',
    )

    riesgo_predicho = models.CharField(max_length=10)
    probabilidad = models.FloatField(null=True, blank=True)

    # XAI — factores clave que más aportaron al diagnóstico
    factores_clave = models.JSONField(null=True, blank=True)

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name_plural = 'Predicciones'

    def __str__(self):
        return f"Paciente {self.paciente_id} → {self.riesgo_predicho}"