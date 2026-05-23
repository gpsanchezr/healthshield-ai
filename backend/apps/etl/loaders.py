import pandas as pd
from django.db import transaction

from .models import Paciente, RegistroClinico, EjecucionETL


class DatabaseLoader:
    def __init__(self, ejecucion: EjecucionETL):
        self.ejecucion = ejecucion

    @transaction.atomic
    def load(self, df: pd.DataFrame) -> int:
        registros_insertados = 0

        # Normalizar nombres de columnas esperadas
        rename_map = {
            'presión_sistólica': 'presion_sistolica',
            'presión_diastólica': 'presion_diastolica',
            'saturación_oxígeno': 'saturacion_oxigeno',
        }
        df = df.rename(columns=rename_map)

        # Columnas que el ETL produce
        df['sexo'] = df.get('sexo')

        for _, row in df.iterrows():
            paciente, _ = Paciente.objects.get_or_create(
                id_paciente_original=int(row['id_paciente']),
                defaults={
                    'nombres': row.get('nombres', '') or '',
                    'apellidos': row.get('apellidos', '') or '',
                    'edad': int(row.get('edad') or 0),
                    'sexo': str(row.get('sexo') or 'M'),
                },
            )

            RegistroClinico.objects.create(
                paciente=paciente,
                peso=row.get('peso'),
                altura=row.get('altura'),
                imc=row.get('IMC') if 'IMC' in row else row.get('imc'),
                clasificacion_imc=row.get('clasificacion_imc'),
                presion_sistolica=row.get('presion_sistolica') if 'presion_sistolica' in row else row.get('presion_sistolica'),
                presion_diastolica=row.get('presion_diastolica') if 'presion_diastolica' in row else row.get('presion_diastolica'),
                frecuencia_cardiaca=row.get('frecuencia_cardiaca'),
                glucosa=row.get('glucosa'),
                colesterol=row.get('colesterol'),
                saturacion_oxigeno=row.get('saturacion_oxigeno'),
                temperatura=row.get('temperatura'),
                antecedentes_familiares=row.get('antecedentes_familiares'),
                fumador=row.get('fumador'),
                consumo_alcohol=row.get('consumo_alcohol'),
                actividad_fisica=row.get('actividad_fisica') if 'actividad_fisica' in row else row.get('actividad_fisica'),
                diagnostico_preliminar=row.get('diagnostico_preliminar') if 'diagnostico_preliminar' in row else row.get('diagnóstico_preliminar'),
                riesgo_enfermedad=row.get('riesgo_enfermedad'),
                fecha_consulta=row.get('fecha_consulta'),
                fuente_etl=self.ejecucion,
            )
            registros_insertados += 1

        return registros_insertados

