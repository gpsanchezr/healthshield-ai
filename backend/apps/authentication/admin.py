from django.contrib import admin

from .models import UsuarioClinico


@admin.register(UsuarioClinico)
class UsuarioClinicoAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "rol", "is_active", "created_at")
    list_filter = ("rol", "is_active")
    search_fields = ("username", "email")
    ordering = ("-created_at",)

