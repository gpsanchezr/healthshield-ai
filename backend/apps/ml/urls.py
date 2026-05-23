from django.urls import path

from .views import (
    PredecirRiesgoView, PredecirSignosView,
    ModeloMetricsView, ModeloActivoMetricsView,
)

urlpatterns = [
    path('ml/predict/paciente/<int:paciente_id>/', PredecirRiesgoView.as_view(), name='ml_predict'),
    path('ml/predict/signos/', PredecirSignosView.as_view(), name='ml_predict_signos'),
    path('ml/modelos/', ModeloMetricsView.as_view(), name='ml_modelos'),
    path('ml/metrics/', ModeloActivoMetricsView.as_view(), name='ml_metrics'),
]