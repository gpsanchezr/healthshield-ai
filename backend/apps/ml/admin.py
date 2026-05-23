from django.contrib import admin

from .models import ModeloML, Prediccion


@admin.register(ModeloML)
class ModeloMLAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "algoritmo",
        "version",
        "accuracy",
        "precision_score",
        "recall",
        "f1_score",
        "entrenado_en",
        "activo",
    )
    list_filter = ("algoritmo", "activo")
    search_fields = ("nombre", "version")
    ordering = ("-entrenado_en",)


@admin.register(Prediccion)
class PrediccionAdmin(admin.ModelAdmin):
    list_display = ("id", "paciente", "modelo", "riesgo_predicho", "probabilidad", "fecha")
    list_filter = ("riesgo_predicho", "fecha")
    search_fields = ("paciente__nombres", "paciente__apellidos", "modelo__nombre")
    raw_id_fields = ("paciente", "modelo")
    ordering = ("-fecha",)

