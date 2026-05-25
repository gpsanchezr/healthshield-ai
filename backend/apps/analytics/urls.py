from django.urls import path

from .views import (
    DashboardKPIsView,
    AlertasListView,
    AlertaMarcarVistaView,
    PacientesSegmentacionView,
    DetectarCriticosView,
    HeatmapCorrelacionView,
)

urlpatterns = [
    path('analytics/kpis/', DashboardKPIsView.as_view(), name='analytics_kpis'),
    path('analytics/alertas/', AlertasListView.as_view(), name='analytics_alertas'),
    path('analytics/alertas/<int:alerta_id>/', AlertaMarcarVistaView.as_view(), name='analytics_alerta_vista'),
    path('analytics/segmentacion/', PacientesSegmentacionView.as_view(), name='analytics_segmentacion'),
    path('analytics/detectar-criticos/', DetectarCriticosView.as_view(), name='analytics_detectar_criticos'),
    path('analytics/correlacion/', HeatmapCorrelacionView.as_view(), name='analytics_correlacion'),
]