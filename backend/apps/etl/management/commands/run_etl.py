# backend/apps/etl/management/commands/run_etl.py
"""
Management command: ejecuta el pipeline ETL desde la línea de comandos.

Uso:
    python manage.py run_etl --file datasets/clinical_data_v1.0_raw.xlsx
    python manage.py run_etl --simulate --count 100
"""
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Ejecuta el pipeline ETL completo sobre un archivo clínico'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', type=str,
            help='Ruta al archivo CSV o Excel a procesar',
        )
        parser.add_argument(
            '--simulate', action='store_true',
            help='Generar e inyectar datos sintéticos en lugar de leer un archivo',
        )
        parser.add_argument(
            '--count', type=int, default=50,
            help='Número de registros a simular (con --simulate)',
        )

    def handle(self, *args, **options):
        from apps.etl.pipeline import ETLPipeline
        from apps.etl.simulation import DataSimulator

        self.stdout.write(self.style.MIGRATE_HEADING('🛡️  HealthShield AI — ETL Pipeline'))

        if options['simulate']:
            self.stdout.write(f"  Generando {options['count']} registros sintéticos...")
            simulator = DataSimulator()
            df = simulator.generate(options['count'])
            pipeline = ETLPipeline(tipo='simulacion')
            result = pipeline.run_dataframe(df)
        elif options['file']:
            source = options['file']
            self.stdout.write(f"  Procesando: {source}")
            pipeline = ETLPipeline(tipo='manual')
            result = pipeline.run(source)
        else:
            raise CommandError("Especifica --file o --simulate")

        if result['status'] == 'success':
            report = result['report']
            self.stdout.write(self.style.SUCCESS(
                f"\n  ✅ ETL completado en {report['duracion_segundos']}s"
            ))
            self.stdout.write(f"  📊 Registros procesados: {report['despues']['total_registros']}")
            self.stdout.write(f"  🧹 Duplicados eliminados: {report['acciones_correctivas'].get('duplicados_eliminados', 0)}")
            self.stdout.write(f"  🔧 Nulos imputados: {report['acciones_correctivas'].get('nulos_imputados', 0)}")
            self.stdout.write(f"  ⭐ Quality Score: {report['quality_score']} ({report['clasificacion']})")
        else:
            self.stdout.write(self.style.ERROR('  ❌ ETL falló'))
