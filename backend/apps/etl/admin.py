from django.contrib import admin

from .models import (
    EjecucionETL,
    LogETL,
    Paciente,
    RegistroClinico,
)


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("id_paciente_original", "nombres", "apellidos", "edad", "sexo", "fecha_registro")
    list_filter = ("sexo", "edad")
    search_fields = ("nombres", "apellidos", "id_paciente_original")
    ordering = ("-fecha_registro",)


@admin.register(EjecucionETL)
class EjecucionETLAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "archivo_fuente",
        "fecha_inicio",
        "fecha_fin",
        "duracion_segundos",
        "registros_extraidos",
        "registros_procesados",
        "registros_rechazados",
        "duplicados_eliminados",
        "nulos_imputados",
        "estado",
        "tipo",
        "usuario",
    )
    list_filter = ("estado", "tipo")
    search_fields = ("archivo_fuente", "usuario__username")
    raw_id_fields = ("usuario",)
    ordering = ("-fecha_inicio",)


@admin.register(LogETL)
class LogETLAdmin(admin.ModelAdmin):
    list_display = ("id", "ejecucion", "nivel", "campo_afectado", "timestamp", "mensaje")
    list_filter = ("nivel", "timestamp")
    search_fields = ("mensaje", "campo_afectado", "ejecucion__id")
    raw_id_fields = ("ejecucion",)


@admin.register(RegistroClinico)
class RegistroClinicoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "paciente",
        "fuente_etl",
        "fecha_consulta",
        "riesgo_enfermedad",
        "imc",
        "clasificacion_imc",
    )
    list_filter = ("riesgo_enfermedad", "fecha_consulta")
    search_fields = (
        "paciente__nombres",
        "paciente__apellidos",
        "paciente__id_paciente_original",
        "diagnostico_preliminar",
    )
    raw_id_fields = ("paciente", "fuente_etl")
    ordering = ("-created_at",)

