"""
Views de Reportes — exportación PDF / Excel / CSV de datos clínicos.
"""
import csv
import io
import json
from datetime import datetime

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.authentication.permissions import EsAnalista, EsAdministrador, EsMedico
from apps.etl.models import Paciente, RegistroClinico
from apps.ml.models import Prediccion


class ExportCSVView(APIView):
    """GET /api/reports/export/csv/ — Exporta pacientes + registros como CSV."""
    permission_classes = [IsAuthenticated, EsAnalista]

    @extend_schema(
        summary="Exportar datos como CSV",
        parameters=[
            OpenApiParameter(name='riesgo', type=str, required=False),
        ],
    )
    def get(self, request):
        riesgo = request.query_params.get('riesgo')

        queryset = RegistroClinico.objects.select_related('paciente').order_by('-fecha_consulta')

        if riesgo:
            queryset = queryset.filter(riesgo_enfermedad=riesgo)

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'id_paciente', 'nombres', 'apellidos', 'edad', 'sexo',
            'imc', 'clasificacion_imc',
            'presion_sistolica', 'presion_diastolica', 'frecuencia_cardiaca',
            'glucosa', 'colesterol',
            'riesgo_enfermedad', 'fecha_consulta',
        ])

        for reg in queryset:
            pac = reg.paciente
            writer.writerow([
                pac.id_paciente_original,
                pac.nombres,
                pac.apellidos,
                pac.edad,
                pac.sexo,
                reg.imc,
                reg.clasificacion_imc,
                reg.presion_sistolica,
                reg.presion_diastolica,
                reg.frecuencia_cardiaca,
                reg.glucosa,
                reg.colesterol,
                reg.riesgo_enfermedad,
                reg.fecha_consulta,
            ])

        output.seek(0)
        response = HttpResponse(output, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="healthshield_report.csv"'
        return response


class ExportExcelView(APIView):
    """GET /api/reports/export/excel/ — Exporta como CSV (Excel-compatible)."""
    permission_classes = [IsAuthenticated, EsAnalista]

    def get(self, request):
        riesgo = request.query_params.get('riesgo')
        queryset = RegistroClinico.objects.select_related('paciente').order_by('-fecha_consulta')

        if riesgo:
            queryset = queryset.filter(riesgo_enfermedad=riesgo)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'ID', 'Nombres', 'Apellidos', 'Edad', 'Sexo',
            'IMC', 'Clasificación IMC',
            'Presión Sist.', 'Presión Diast.', 'FC',
            'Glucosa', 'Colesterol',
            'Riesgo', 'Fecha Consulta',
        ])

        for reg in queryset:
            pac = reg.paciente
            writer.writerow([
                pac.id_paciente_original,
                pac.nombres,
                pac.apellidos,
                pac.edad,
                pac.sexo,
                reg.imc,
                reg.clasificacion_imc,
                reg.presion_sistolica,
                reg.presion_diastolica,
                reg.frecuencia_cardiaca,
                reg.glucosa,
                reg.colesterol,
                reg.riesgo_enfermedad,
                reg.fecha_consulta,
            ])

        output.seek(0)
        response = HttpResponse(output, content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="healthshield_report.xlsx"'
        return response


class PacienteDetallePDFView(APIView):
    """GET /api/reports/paciente/{id}/ — Genera resumen clínico del paciente."""
    permission_classes = [IsAuthenticated, EsMedico]

    @extend_schema(summary="Detalle clínico de paciente (texto)")
    def get(self, request, paciente_id):
        try:
            paciente = Paciente.objects.get(id=paciente_id)
        except Paciente.DoesNotExist:
            return Response({'error': 'Paciente no encontrado'}, status=404)

        registros = RegistroClinico.objects.filter(paciente=paciente).order_by('-fecha_consulta')
        predicciones = Prediccion.objects.filter(paciente=paciente).order_by('-fecha')[:3]

        # Armar resumen
        ultimo = registros.first()
        context = {
            'paciente': {
                'id': paciente.id,
                'nombre': str(paciente),
                'edad': paciente.edad,
                'sexo': paciente.sexo,
            },
            'ultimo_registro': {
                'fecha': ultimo.fecha_consulta if ultimo else None,
                'imc': ultimo.imc if ultimo else None,
                'glucosa': ultimo.glucosa if ultimo else None,
                'presion': f"{ultimo.presion_sistolica}/{ultimo.presion_diastolica}" if ultimo else None,
                'riesgo': ultimo.riesgo_enfermedad if ultimo else None,
            },
            'total_registros': registros.count(),
            'predicciones_recientes': [
                {
                    'fecha': p.fecha,
                    'riesgo': p.riesgo_predicho,
                    'probabilidad': p.probabilidad,
                    'factores': p.factores_clave,
                }
                for p in predicciones
            ],
        }

        return Response(context)


class ExportPDFView(APIView):
    """GET /api/reports/export/pdf/ — Genera informe clínico completo en PDF."""
    permission_classes = [IsAuthenticated, EsAnalista]

    @extend_schema(
        summary="Exportar reporte clínico en PDF",
        description="Genera un documento PDF con resumen de pacientes, distribución de riesgo y estadísticas clínicas.",
    )
    def get(self, request):
        riesgo = request.query_params.get('riesgo')

        queryset = RegistroClinico.objects.select_related('paciente').order_by('-fecha_consulta')
        if riesgo:
            queryset = queryset.filter(riesgo_enfermedad=riesgo)

        # Prepare data for PDF
        total_pacientes = Paciente.objects.count()
        total_registros = RegistroClinico.objects.count()
        from django.db.models import Avg
        stats = RegistroClinico.objects.aggregate(
            avg_imc=Avg('imc'),
            avg_glucosa=Avg('glucosa'),
            avg_ps=Avg('presion_sistolica'),
        )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=0.75*inch, rightMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                      fontSize=18, spaceAfter=12,
                                      textColor=colors.HexColor('#0d6efd'))
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                        fontSize=11, textColor=colors.grey,
                                        spaceAfter=20)
        header_style = ParagraphStyle('Header', parent=styles['Heading2'],
                                      fontSize=12, spaceAfter=8,
                                      textColor=colors.HexColor('#0d6efd'))

        elements = []

        # ── Título ──
        elements.append(Paragraph("HealthShield AI — Informe Clínico", title_style))
        elements.append(Paragraph(
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
            f"Total pacientes: {total_pacientes} | Registros: {total_registros}",
            subtitle_style))
        elements.append(Spacer(1, 0.1*inch))

        # ── Resumen Ejecutivo ──
        elements.append(Paragraph("Resumen Ejecutivo", header_style))
        kpi_data = [
            ['Métrica', 'Valor'],
            ['Total Pacientes', str(total_pacientes)],
            ['Total Registros Clínicos', str(total_registros)],
            ['IMC Promedio', f"{float(stats['avg_imc'] or 0):.2f}"],
            ['Glucosa Promedio (mg/dL)', f"{float(stats['avg_glucosa'] or 0):.2f}"],
            ['Presión Sistólica Promedio (mmHg)', f"{float(stats['avg_ps'] or 0):.2f}"],
        ]
        kpi_table = Table(kpi_data, colWidths=[3*inch, 3*inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 0.3*inch))

        # ── Tabla de Registros ──
        elements.append(Paragraph("Détail des Registres Cliniques", header_style))

        page_limit = min(len(queryset), 100)
        table_data = [['Paciente', 'Edad', 'IMC', 'Glucosa', 'Presión', 'Riesgo']]
        for reg in queryset[:page_limit]:
            pac = reg.paciente
            table_data.append([
                f"{pac.nombres} {pac.apellidos[:15]}",
                str(pac.edad),
                f"{reg.imc or '-':.1f}",
                f"{reg.glucosa or '-':.1f}",
                f"{reg.presion_sistolica or '-'}/{reg.presion_diastolica or '-'}",
                reg.riesgo_enfermedad or '-',
            ])

        reg_table = Table(table_data, colWidths=[2.2*inch, 0.6*inch, 0.7*inch, 0.8*inch, 1.1*inch, 0.8*inch])
        reg_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(reg_table)

        if len(queryset) > page_limit:
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(
                f"<i>* Mostrando {page_limit} de {len(queryset)} registros. "
                f"Usa la exportación CSV para datos completos.</i>",
                styles['Normal']))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        response = HttpResponse(buffer.read(), content_type='application/pdf')
        filename = f"healthshield_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response