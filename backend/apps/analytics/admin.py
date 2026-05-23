from django.contrib import admin

from .models import Alerta


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "paciente",
        "tipo_alerta",
        "nivel_urgencia",
        "visto_por",
        "fecha_alerta",
        "fecha_vista",
    )
    list_filter = ("nivel_urgencia", "fecha_alerta")
    search_fields = ("tipo_alerta", "descripcion", "paciente__nombres", "paciente__apellidos")
    raw_id_fields = ("paciente", "visto_por")
    ordering = ("-fecha_alerta",)

