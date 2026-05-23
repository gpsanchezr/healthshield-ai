from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RunETLView, SimulateDataView, HistorialETLView, CalidadReporteView,
    PacienteViewSet, RegistroClinicoViewSet,
)

router = DefaultRouter()
router.register(r'pacientes', PacienteViewSet, basename='paciente')
router.register(r'registros', RegistroClinicoViewSet, basename='registro')

urlpatterns = [
    path('etl/run/', RunETLView.as_view(), name='etl_run'),
    path('etl/simular/', SimulateDataView.as_view(), name='etl_simulate'),
    path('etl/historial/', HistorialETLView.as_view(), name='etl_history'),
    path('etl/calidad/<int:ejecucion_id>/', CalidadReporteView.as_view(), name='etl_quality'),
    path('', include(router.urls)),
]