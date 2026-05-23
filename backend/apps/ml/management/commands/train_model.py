"""
Management command: entrena el modelo de Machine Learning.

Uso:
    python manage.py train_model --algorithm random_forest
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Entrena el modelo de Machine Learning con los datos limpios en BD'

    def add_arguments(self, parser):
        parser.add_argument(
            '--algorithm', type=str, default='random_forest',
            choices=['random_forest', 'logistic_regression', 'decision_tree'],
            help='Algoritmo de Machine Learning a usar',
        )

    def handle(self, *args, **options):
        import pandas as pd
        from apps.ml.trainer import ModelTrainer

        self.stdout.write(self.style.MIGRATE_HEADING('🤖  HealthShield AI — ML Trainer'))

        # Cargar datos limpios desde BD
        from apps.etl.models import RegistroClinico
        qs = RegistroClinico.objects.all().values(
            'imc', 'presion_sistolica', 'presion_diastolica',
            'frecuencia_cardiaca', 'glucosa', 'colesterol',
            'saturacion_oxigeno', 'temperatura',
            'fumador', 'consumo_alcohol', 'antecedentes_familiares',
            'riesgo_enfermedad', 'paciente__edad',
        )

        if not qs.exists():
            self.stdout.write(self.style.ERROR('  ❌ No hay datos en BD. Ejecuta primero: python manage.py run_etl'))
            return

        df = pd.DataFrame(list(qs))
        df = df.rename(columns={'paciente__edad': 'edad'})

        self.stdout.write(f"  📊 Datos cargados: {len(df)} registros")

        trainer = ModelTrainer(algorithm=options['algorithm'])
        result = trainer.train(df)

        # Guardar en BD
        from apps.ml.models import ModeloML
        ModeloML.objects.filter(activo=True).update(activo=False)
        ModeloML.objects.create(
            nombre=f"HealthShield {options['algorithm'].replace('_', ' ').title()}",
            algoritmo=options['algorithm'],
            version=f"v1.{ModeloML.objects.count() + 1}",
            accuracy=result['accuracy'],
            precision_score=result['precision'],
            recall=result['recall'],
            f1_score=result['f1_score'],
            archivo_modelo=result['model_path'],
            feature_names=result['features'],
            feature_importance=result['feature_importance'],
            registros_entrenamiento=result['training_samples'],
            activo=True,
        )

        self.stdout.write(self.style.SUCCESS(f"\n  ✅ Modelo entrenado exitosamente"))
        self.stdout.write(f"  🎯 Accuracy:   {result['accuracy']}")
        self.stdout.write(f"  🎯 Precision:  {result['precision']}")
        self.stdout.write(f"  🎯 Recall:     {result['recall']}")
        self.stdout.write(f"  🎯 F1-Score:   {result['f1_score']}")
        self.stdout.write(f"  🎯 CV Accuracy:{result['cv_accuracy']} (validación cruzada 5-fold)")
        self.stdout.write(f"\n  📁 Modelo guardado en: {result['model_path']}")
        self.stdout.write(f"\n  🔍 Top 3 variables predictoras:")
        for feat, imp in list(result['feature_importance'].items())[:3]:
            self.stdout.write(f"     • {feat}: {imp:.4f}")
