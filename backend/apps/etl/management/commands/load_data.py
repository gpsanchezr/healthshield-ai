from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from apps.etl.pipeline import ETLPipeline


class Command(BaseCommand):
    help = "Carga masiva de datos clínicos usando el pipeline ETL existente"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="Ruta al archivo CSV o Excel")

    def handle(self, *args, **kwargs):
        file_path = kwargs["file_path"]
        self.stdout.write(self.style.MIGRATE_HEADING(f"Iniciando ETL sobre: {file_path}"))

        try:
            pipeline = ETLPipeline(tipo='manual')
            result = pipeline.run(file_path)

            if result.get('status') != 'success':
                raise CommandError("El pipeline ETL no devolvió un resultado válido")

            report = result['report']
            self.stdout.write(self.style.SUCCESS("¡Éxito! El archivo fue procesado correctamente."))
            self.stdout.write(f"  Registros extraídos: {report['antes']['total_registros']}")
            self.stdout.write(f"  Registros cargados: {report['despues']['total_registros']}")
            self.stdout.write(f"  Duplicados eliminados: {report['acciones_correctivas'].get('duplicados_eliminados', 0)}")
            self.stdout.write(f"  Nulos imputados: {report['acciones_correctivas'].get('nulos_imputados', 0)}")
            self.stdout.write(f"  Quality Score: {report.get('quality_score', 'N/A')} ({report.get('clasificacion', 'N/A')})")

        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Error durante la carga: {exc}"))
            raise

