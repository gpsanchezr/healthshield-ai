from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class Paciente(models.Model):
    GENERO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino')]

    # Campos compatibles con el migration 0001_initial.py
    id_paciente_original = models.IntegerField(unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    edad = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(120)])
    sexo = models.CharField(max_length=1, choices=GENERO_CHOICES)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"



class EjecucionETL(models.Model):
    ESTADO_CHOICES = [
        ('en_proceso', 'en_proceso'),
        ('completado', 'completado'),
        ('fallido', 'fallido'),
    ]

    archivo_fuente = models.CharField(max_length=255, null=True, blank=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    duracion_segundos = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)

    registros_extraidos = models.IntegerField(default=0)
    registros_procesados = models.IntegerField(default=0)
    registros_rechazados = models.IntegerField(default=0)
    duplicados_eliminados = models.IntegerField(default=0)
    nulos_imputados = models.IntegerField(default=0)

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='en_proceso')
    reporte_calidad = models.JSONField(null=True, blank=True)

    TIPO_CHOICES = [
        ('manual', 'manual'),
        ('simulacion', 'simulacion'),
        ('automatico', 'automatico'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='manual')

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='etl_ejecuciones',
    )



class LogETL(models.Model):
    NIVEL_CHOICES = [
        ('INFO', 'INFO'),
        ('WARNING', 'WARNING'),
        ('ERROR', 'ERROR'),
    ]

    ejecucion = models.ForeignKey(EjecucionETL, related_name='logs', on_delete=models.CASCADE)
    nivel = models.CharField(max_length=10, choices=NIVEL_CHOICES)
    mensaje = models.TextField()
    campo_afectado = models.CharField(max_length=50, null=True, blank=True)

    valor_original = models.TextField(null=True, blank=True)
    valor_corregido = models.TextField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)


class RegistroClinico(models.Model):
    RIESGO_CHOICES = [
        ('Bajo', 'Bajo'),
        ('Medio', 'Medio'),
        ('Alto', 'Alto'),
        ('Crítico', 'Crítico'),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='registros',
    )

    # Campos compatibles con migration 0001_initial.py
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(20), MaxValueValidator(300)])
    altura = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0.5), MaxValueValidator(2.5)])
    imc = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    clasificacion_imc = models.CharField(max_length=20, null=True, blank=True)

    presion_sistolica = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(60), MaxValueValidator(250)])
    presion_diastolica = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(40), MaxValueValidator(150)])
    frecuencia_cardiaca = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(30), MaxValueValidator(220)])

    glucosa = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(50), MaxValueValidator(600)])
    colesterol = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    saturacion_oxigeno = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temperatura = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    antecedentes_familiares = models.BooleanField(null=True, blank=True)
    fumador = models.BooleanField(null=True, blank=True)
    consumo_alcohol = models.BooleanField(null=True, blank=True)

    actividad_fisica = models.CharField(max_length=20, null=True, blank=True)
    diagnostico_preliminar = models.CharField(max_length=100, null=True, blank=True)

    riesgo_enfermedad = models.CharField(max_length=10, null=True, blank=True, choices=RIESGO_CHOICES)
    fecha_consulta = models.DateField(null=True, blank=True)

    # Origen del ETL (compatible con migration 0001_initial.py)
    fuente_etl = models.ForeignKey(
        EjecucionETL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='registros',
    )


    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        fecha = self.fecha_consulta.strftime('%Y-%m-%d') if self.fecha_consulta else 'sin-fecha'
        return f"Registro de {self.paciente} - {fecha}"


    class Meta:
        verbose_name = "Registro Clínico"
        verbose_name_plural = "Registros Clínicos"

