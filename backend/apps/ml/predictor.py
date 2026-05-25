import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from django.conf import settings

from .models import ModeloML

logger = logging.getLogger('ml')


class ModelPredictor:
    """Realiza inferencia ML con explicabilidad XAI (top-3 features)."""

    RISK_LABELS = {0: 'Bajo', 1: 'Medio', 2: 'Alto', 3: 'Crítico'}
    TOP_N_FEATURES = 3

    def __init__(self):
        self.model = None
        self.feature_names = None
        self._load_active_model()

    def _load_active_model(self):
        """Carga el modelo activo desde la BD o disco."""
        try:
            ml_record = ModeloML.objects.filter(activo=True).order_by('-entrenado_en').first()
        except Exception:
            ml_record = None

        if ml_record and ml_record.archivo_modelo:
            try:
                filepath = Path(ml_record.archivo_modelo)
                if filepath.exists():
                    payload = joblib.load(filepath)
                    self.model = payload['model']
                    self.feature_names = payload['feature_names']
                    logger.info(f"[Predictor] Modelo cargado: {ml_record.nombre}")
                    return
            except Exception as e:
                logger.warning(f"[Predictor] No se pudo cargar modelo desde disco: {e}")

        logger.warning("[Predictor] Usando modelo por defecto (sin entrenamiento real)")
        self.model = None
        self.feature_names = None

    def predict(self, registro_data: dict) -> dict:
        """
        Realiza predicción para un paciente.

        Args:
            registro_data: dict con claves de feature (imc, presion_sistolica, etc.)

        Returns:
            dict con riesgo_predicho, probabilidad y factores_clave (XAI)
        """
        if self.model is None:
            return self._mock_prediction(registro_data)

        # Construir vector de features
        X = self._build_feature_vector(registro_data)

        # Predicción de clase
        pred_class = int(self.model.predict(X)[0])
        riesgo = self.RISK_LABELS.get(pred_class, 'Bajo')

        # Probabilidades por clase
        probabilities = self.model.predict_proba(X)[0]
        prob_dict = {self.RISK_LABELS[i]: round(float(p), 4) for i, p in enumerate(probabilities)}

        # Factores clave (XAI simplificado vía feature importance)
        factores = self._get_top_features(X)

        logger.info(f"[Predictor] Paciente → {riesgo} (confianza={prob_dict[riesgo]})")

        return {
            'riesgo_predicho': riesgo,
            'probabilidades': prob_dict,
            'factores_clave': factores,
        }

    def _build_feature_vector(self, data: dict) -> np.ndarray:
        """Construye array numpy ordenado según feature_names del modelo."""
        if self.feature_names is None:
            raise ValueError("No hay modelo cargado.")

        values = []
        for feat in self.feature_names:
            val = data.get(feat, np.nan)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                # Medianadummy para datos faltantes
                val = 0.0
            
            try:
                val = float(val)
            except (ValueError, TypeError):
                val = 0.0
                
            values.append(val)

        X = np.array(values).reshape(1, -1)
        return X

    def _get_top_features(self, X: np.ndarray) -> list:
        """Retorna las N features con mayor importancia/impacto en la predicción."""
        if self.feature_names is None:
            return []

        try:
            # Feature importance del modelo
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
            elif hasattr(self.model, 'coef_'):
                importances = np.abs(self.model.coef_[0])
            else:
                return []

            # Ordenar por importancia
            indexed = list(zip(self.feature_names, importances))
            ranked = sorted(indexed, key=lambda x: x[1], reverse=True)

            factores = []
            for feat_name, importance in ranked[:self.TOP_N_FEATURES]:
                factores.append({
                    'variable': feat_name,
                    'impacto': round(float(importance), 4),
                    'direccion': 'aumenta_riesgo' if importance > 0.05 else 'neutro',
                })
            return factores

        except Exception as e:
            logger.error(f"[Predictor] Error calculando factores clave: {e}")
            return []

    def _mock_prediction(self, data: dict) -> dict:
        """Predicción mock cuando no hay modelo entrenado."""
        score = 0
        # Glucosa: >200 alto, >150 moderado
        glu = data.get('glucosa', 0) or 0
        if glu > 200:
            score += 2
        elif glu > 150:
            score += 1

        # Presión sistólica: >140 alto, >130 moderado
        ps = data.get('presion_sistolica', 0) or 0
        if ps > 140:
            score += 2
        elif ps > 130:
            score += 1

        # IMC: >30 alto, >25 moderado
        imc_val = data.get('IMC', 0) or data.get('imc', 0) or 0
        if imc_val > 30:
            score += 2
        elif imc_val > 25:
            score += 1

        if score >= 4:
            riesgo = 'Alto'
        elif score >= 2:
            riesgo = 'Medio'
        else:
            riesgo = 'Bajo'

        return {
            'riesgo_predicho': riesgo,
            'probabilidades': {'Bajo': 0.6, 'Medio': 0.3, 'Alto': 0.08, 'Crítico': 0.02},
            'factores_clave': [
                {'variable': 'glucosa', 'impacto': 0.25, 'direccion': 'aumenta_riesgo'},
                {'variable': 'presion_sistolica', 'impacto': 0.20, 'direccion': 'aumenta_riesgo'},
                {'variable': 'imc', 'impacto': 0.15, 'direccion': 'aumenta_riesgo'},
            ],
        }


def get_predictor() -> ModelPredictor:
    """Factory para obtener instancia del predictor (singleton por request)."""
    return ModelPredictor()