"""
Tests para el módulo de Machine Learning (trainer y predictor).
"""
import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from apps.ml.predictor import ModelPredictor


class TestModelPredictor:
    """Tests del predictor — inferencia ML."""

    def test_mock_prediction_alto_riesgo(self):
        """Glucosa > 200 y presión > 140 → riesgo Alto."""
        predictor = ModelPredictor()
        data = {
            'glucosa': 250,
            'presion_sistolica': 160,
            'IMC': 28,
        }
        result = predictor.predict(data)

        assert result['riesgo_predicho'] == 'Alto'
        assert 'factores_clave' in result
        assert 'probabilidades' in result
        assert len(result['factores_clave']) <= 3

    def test_mock_prediction_bajo_riesgo(self):
        """Valores normales → riesgo Bajo."""
        predictor = ModelPredictor()
        data = {
            'glucosa': 100,
            'presion_sistolica': 115,
            'IMC': 23,
        }
        result = predictor.predict(data)

        assert result['riesgo_predicho'] == 'Bajo'
        assert 'factores_clave' in result

    def test_mock_prediction_medio_riesgo(self):
        """Glucosa moderadamente elevada → riesgo Medio."""
        predictor = ModelPredictor()
        data = {
            'glucosa': 160,
            'presion_sistolica': 130,
            'IMC': 26,
        }
        result = predictor.predict(data)

        assert result['riesgo_predicho'] == 'Medio'

    def test_probabilidades_sum_one(self):
        """Las probabilidades deben sumar ~1.0."""
        predictor = ModelPredictor()
        data = {
            'glucosa': 200,
            'presion_sistolica': 150,
            'IMC': 30,
        }
        result = predictor.predict(data)

        probs = result['probabilidades']
        total = sum(probs.values())
        assert abs(total - 1.0) < 0.05, f"Probabilidades suman {total}, esperado ~1.0"

    def test_factores_clave_contains_variable(self):
        """Factores clave deben incluir variables relevantes."""
        predictor = ModelPredictor()
        data = {
            'glucosa': 250,
            'presion_sistolica': 160,
            'IMC': 30,
        }
        result = predictor.predict(data)

        variables = [f['variable'] for f in result['factores_clave']]
        assert 'glucosa' in variables or 'presion_sistolica' in variables

    def test_imc_key_variations(self):
        """Variaciones de IMC (imc vs IMC) son procesadas."""
        predictor = ModelPredictor()

        result_upper = predictor.predict({'IMC': 35, 'glucosa': 100, 'presion_sistolica': 110})
        result_lower = predictor.predict({'imc': 35, 'glucosa': 100, 'presion_sistolica': 110})

        assert result_upper['riesgo_predicho'] in ['Medio', 'Alto', 'Crítico']
        assert result_lower['riesgo_predicho'] in ['Medio', 'Alto', 'Crítico']

    def test_predictor_factory(self):
        """get_predictor factory retorna instancia válida."""
        from apps.ml.predictor import get_predictor
        predictor = get_predictor()

        assert isinstance(predictor, ModelPredictor)
        assert hasattr(predictor, 'predict')


class TestModelTrainerIntegration:
    """Tests de integración del ModelTrainer — requieren sklearn."""

    def test_prepare_features_extracts_valid_columns(self, df_minimal):
        """_prepare_features filtra solo columnas disponibles y convierte target a numérico."""
        from apps.ml.trainer import ModelTrainer

        trainer = ModelTrainer(algorithm='random_forest')
        X, y, feature_names = trainer._prepare_features(df_minimal)

        assert len(X) == len(y)
        assert len(X) == 5
        assert set(y).issubset({0, 1, 2, 3})
        assert all(col in df_minimal.columns for col in feature_names)

    def test_prepare_features_removes_rows_without_target(self):
        """Filas sin riesgo_enfermedad son excluidas."""
        from apps.ml.trainer import ModelTrainer

        df = pd.DataFrame({
            'imc': [23.5, 28.1, 19.2],
            'presion_sistolica': [115, 155, 108],
            'glucosa': [95.0, 260.0, 88.0],
            'riesgo_enfermedad': ['Bajo', None, 'Alto'],  # una fila sin target
        })
        trainer = ModelTrainer(algorithm='random_forest')
        X, y, _ = trainer._prepare_features(df)

        assert len(X) == 2

    def test_train_returns_complete_metrics(self, df_minimal):
        """train() retorna todas las métricas esperadas."""
        from apps.ml.trainer import ModelTrainer

        trainer = ModelTrainer(algorithm='random_forest')
        result = trainer.train(df_minimal)

        assert 'accuracy' in result
        assert 'f1_score' in result
        assert 'precision' in result
        assert 'recall' in result
        assert 'cv_accuracy' in result
        assert 'model_path' in result
        assert 'features' in result
        assert 'feature_importance' in result
        assert 'classification_report' in result

        # Todas las métricas entre 0 y 1
        assert 0 <= result['accuracy'] <= 1
        assert 0 <= result['f1_score'] <= 1

    def test_train_random_forest_algorithm(self, df_minimal):
        """Entrenamiento con random_forest produce un modelo con feature_importances_."""
        from apps.ml.trainer import ModelTrainer

        trainer = ModelTrainer(algorithm='random_forest')
        result = trainer.train(df_minimal)

        assert result['accuracy'] > 0
        assert len(result['feature_importance']) > 0

    def test_train_logistic_regression_algorithm(self, df_minimal):
        """Entrenamiento con logistic_regression funciona sin errores."""
        from apps.ml.trainer import ModelTrainer

        trainer = ModelTrainer(algorithm='logistic_regression')
        result = trainer.train(df_minimal)

        assert 'accuracy' in result
        assert result['accuracy'] >= 0

    def test_train_decision_tree_algorithm(self, df_minimal):
        """Entrenamiento con decision_tree funciona."""
        from apps.ml.trainer import ModelTrainer

        trainer = ModelTrainer(algorithm='decision_tree')
        result = trainer.train(df_minimal)

        assert 'accuracy' in result

    def test_invalid_algorithm_raises(self):
        """Pasar un algoritmo inválido lanza ValueError."""
        from apps.ml.trainer import ModelTrainer

        with pytest.raises(ValueError, match="Algoritmo desconocido"):
            ModelTrainer(algorithm='invalid_algorithm')

    def test_boolean_columns_converted_to_int(self, df_minimal):
        """Columnas booleanas son convertidas a 0/1 en _prepare_features."""
        from apps.ml.trainer import ModelTrainer

        trainer = ModelTrainer(algorithm='random_forest')
        X, _, _ = trainer._prepare_features(df_minimal)

        for col in ['fumador', 'consumo_alcohol', 'antecedentes_familiares']:
            if col in X.columns:
                assert X[col].dtype in [np.int64, np.int32, int]
                assert X[col].isin([0, 1]).all()