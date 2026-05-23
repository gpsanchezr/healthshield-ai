from django.urls import path

from .views import ExportCSVView, ExportExcelView, ExportPDFView, PacienteDetallePDFView

urlpatterns = [
    path('reports/export/csv/', ExportCSVView.as_view(), name='reports_export_csv'),
    path('reports/export/excel/', ExportExcelView.as_view(), name='reports_export_excel'),
    path('reports/export/pdf/', ExportPDFView.as_view(), name='reports_export_pdf'),
    path('reports/paciente/<int:paciente_id>/', PacienteDetallePDFView.as_view(), name='reports_paciente'),
]