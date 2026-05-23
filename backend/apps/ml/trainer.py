import logging
import os
import pickle
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, KFold
from sklearn.tree import DecisionTreeClassifier

logger = logging.getLogger('ml')


class ModelTrainer:
    """Orquestador de entrenamiento de modelos de clasificación clínica."""

    ALGORITHMS = {
        'random_forest': RandomForestClassifier,
        'logistic_regression': LogisticRegression,
        'decision_tree': DecisionTreeClassifier,
    }

    TARGET_COLUMN = 'riesgo_enfermedad'

    # Features usados para entrenar
    FEATURE_COLUMNS = [
        'imc',
        'presion_sistolica',
        'presion_diastolica',
        'frecuencia_cardiaca',
        'glucosa',
        'colesterol',
        'saturacion_oxigeno',
        'temperatura',
        'fumador',
        'consumo_alcohol',
        'antecedentes_familiares',
        'edad',
    ]

    def __init__(self, algorithm: str = 'random_forest'):
        if algorithm not in self.ALGORITHMS:
            raise ValueError(f"Algoritmo desconocido: {algorithm}")
        self.algorithm = algorithm

        # Crear directorio de modelos si no existe
        models_path = Path(settings.ML_MODELS_PATH)
        models_path.mkdir(parents=True, exist_ok=True)
        self.models_path = models_path

    def train(self, df: pd.DataFrame) -> dict:
        """Ejecuta el pipeline completo de entrenamiento."""
        logger.info(f"[ML Trainer] Iniciando entrenamiento con {self.ALGORITHMS[self.algorithm].__name__}")

        # 1. Preparar features y target
        X, y, feature_names = self._prepare_features(df)

        # 2. Split estratificado 80/20 cuando es posible
        from sklearn.model_selection import train_test_split

        unique_labels, counts = np.unique(y, return_counts=True)
        stratify_arg = y if len(unique_labels) > 1 and counts.min() > 1 else None
        split_kwargs = {'test_size': 0.2, 'random_state': 42}
        if stratify_arg is not None:
            split_kwargs['stratify'] = stratify_arg

        X_train, X_test, y_train, y_test = train_test_split(X, y, **split_kwargs)

        # 3. Instanciar modelo con class_weight='balanced'
        model_class = self.ALGORITHMS[self.algorithm]
        if self.algorithm == 'random_forest':
            model = model_class(
                n_estimators=200,
                max_depth=10,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1,
            )
        elif self.algorithm == 'logistic_regression':
            model = model_class(class_weight='balanced', max_iter=1000, random_state=42)
        else:
            model = model_class(class_weight='balanced', random_state=42)

        # 4. Entrenar
        model.fit(X_train, y_train)

        # 5. Predecir en test set
        y_pred = model.predict(X_test)

        # 6. Métricas
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

        # 7. Validación cruzada segura
        unique_labels, counts = np.unique(y, return_counts=True)
        if len(y) >= 2 and counts.min() > 1:
            n_splits = min(5, int(counts.min()), len(y))
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        elif len(y) >= 2:
            n_splits = min(2, len(y))
            cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        else:
            cv = None

        if cv is not None:
            cv_scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy')
            cv_accuracy_mean = float(np.mean(cv_scores))
            cv_accuracy_std = float(np.std(cv_scores))
        else:
            cv_accuracy_mean = float(accuracy)
            cv_accuracy_std = 0.0

        logger.info(f"[ML] Accuracy={accuracy:.4f} | F1={f1:.4f} | CV={cv_accuracy_mean:.4f}±{cv_accuracy_std:.4f}")

        # 8. Feature importance
        if hasattr(model, 'feature_importances_'):
            importance = dict(zip(feature_names, model.feature_importances_.tolist()))
        else:
            importance = {}

        # 9. Guardar modelo
        model_path = self._save_model(model, feature_names)

        # 10. Classification report
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        return {
            'accuracy': round(accuracy, 4),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
            'cv_accuracy': round(cv_accuracy_mean, 4),
            'cv_accuracy_std': round(cv_accuracy_std, 4),
            'model_path': str(model_path),
            'features': feature_names,
            'feature_importance': importance,
            'training_samples': len(X_train),
            'classification_report': report,
        }

    def _prepare_features(self, df: pd.DataFrame) -> tuple:
        """Preprocesa el DataFrame y retorna (X, y, feature_names)."""
        # Filtrar solo filas con target válido
        df = df[df[self.TARGET_COLUMN].notna()].copy()

        # Mapear target a numérico para entrenamiento
        risk_mapping = {'Bajo': 0, 'Medio': 1, 'Alto': 2, 'Crítico': 3}
        df['_target_num'] = df[self.TARGET_COLUMN].map(risk_mapping)
        df = df[df['_target_num'].notna()].copy()

        # Seleccionar features disponibles
        available_features = [c for c in self.FEATURE_COLUMNS if c in df.columns]

        X = df[available_features].copy()
        y = df['_target_num'].astype(int)

        # Preprocesar X
        X = X.fillna(X.median())

        # Asegurar booleanos como 0/1
        for col in ['fumador', 'consumo_alcohol', 'antecedentes_familiares']:
            if col in X.columns:
                X[col] = X[col].astype(int)

        return X, y.values, available_features

    def _save_model(self, model, feature_names: list) -> Path:
        """Persiste el modelo entrenado en disco como .pkl."""
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        filename = f"model_{self.algorithm}_{timestamp}.pkl"
        filepath = self.models_path / filename

        payload = {
            'model': model,
            'feature_names': feature_names,
            'algorithm': self.algorithm,
        }
        joblib.dump(payload, filepath)
        logger.info(f"[ML] Modelo guardado en: {filepath}")
        return filepath


def train_risk_model(df: pd.DataFrame, algorithm: str = 'random_forest') -> dict:
    """
    Función de alto nivel para entrenar y persistir un modelo de riesgo clínico.

    Uso directo (fuera de Django manage.py):
        from apps.ml.trainer import train_risk_model
        import pandas as pd
        df = pd.read_excel('datos_limpios.xlsx')
        resultado = train_risk_model(df, algorithm='random_forest')
        print(resultado['accuracy'], resultado['model_path'])

    Uso via API:
        GET/POST /api/ml/entrenar/
    """
    trainer = ModelTrainer(algorithm=algorithm)
    return trainer.train(df)