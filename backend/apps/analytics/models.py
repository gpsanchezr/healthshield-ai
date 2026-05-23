from django.db import models


class Alerta(models.Model):
    """Alertas proactivas generadas por规则 clínicas sobre pacientes críticos."""

    URGENCIA_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    paciente = models.ForeignKey(
        'etl.Paciente',
        on_delete=models.CASCADE,
        related_name='alertas',
    )
    tipo_alerta = models.CharField(max_length=50)
    descripcion = models.TextField()
    nivel_urgencia = models.CharField(max_length=10, choices=URGENCIA_CHOICES, default='media')

    # Seguimiento
    visto_por = models.ForeignKey(
        'authentication.UsuarioClinico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertas_vistas',
    )
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    fecha_vista = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_alerta']
        verbose_name_plural = 'Alertas'

    def __str__(self):
        return f"[{self.nivel_urgencia}] {self.tipo_alerta} - Paciente {self.paciente_id}"