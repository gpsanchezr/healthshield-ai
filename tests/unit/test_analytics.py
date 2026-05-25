"""
Tests para los calculators de analítica clínica.
"""
from unittest.mock import MagicMock



class TestPacienteCriticoDetector:
    """Tests del detector de pacientes críticos."""

    def test_detects_high_glucose(self):
        """Glucosa > 300 mg/dL → alerta."""
        from apps.analytics.calculators import PacienteCriticoDetector

        detector = PacienteCriticoDetector()

        assert detector.GLUCOSA_CRITICA == 300
        record = MagicMock()
        record.glucosa = 350
        record.presion_sistolica = 120
        record.saturacion_oxigeno = 98
        record.riesgo_enfermedad = 'Bajo'
        record.paciente_id = 1

        desc = detector._build_description(record)
        assert 'Glucosa elevada' in desc

    def test_detects_high_pressure(self):
        """Presión sistólica > 180 → alerta."""
        from apps.analytics.calculators import PacienteCriticoDetector

        detector = PacienteCriticoDetector()
        record = MagicMock()
        record.glucosa = 100
        record.presion_sistolica = 190
        record.saturacion_oxigeno = 98
        record.riesgo_enfermedad = 'Bajo'
        record.paciente_id = 2

        desc = detector._build_description(record)
        assert 'Presión sistólica alta' in desc

    def test_detects_low_saturation(self):
        """Saturación O2 < 85% → alerta."""
        from apps.analytics.calculators import PacienteCriticoDetector

        detector = PacienteCriticoDetector()
        record = MagicMock()
        record.glucosa = 100
        record.presion_sistolica = 120
        record.saturacion_oxigeno = 80
        record.riesgo_enfermedad = 'Bajo'
        record.paciente_id = 3

        desc = detector._build_description(record)
        assert 'Saturación de oxígeno baja' in desc

    def test_multiple_conditions_all_reported(self):
        """Cuando hay varias condiciones críticas, todas aparecen en descripción."""
        from apps.analytics.calculators import PacienteCriticoDetector

        detector = PacienteCriticoDetector()
        record = MagicMock()
        record.glucosa = 350
        record.presion_sistolica = 190
        record.saturacion_oxigeno = 80
        record.riesgo_enfermedad = 'Alto'
        record.paciente_id = 4

        desc = detector._build_description(record)
        assert 'Glucosa elevada' in desc
        assert 'Presión sistólica alta' in desc
        assert 'Saturación de oxígeno baja' in desc

    def test_build_description_default_when_no_specific(self):
        """Si no hay condición específica conocida, usa mensaje genérico."""
        from apps.analytics.calculators import PacienteCriticoDetector

        detector = PacienteCriticoDetector()
        record = MagicMock()
        record.glucosa = 295  # bajo el umbral
        record.presion_sistolica = 175  # bajo el umbral
        record.saturacion_oxigeno = 88  # sobre el umbral
        record.riesgo_enfermedad = 'Alto'
        record.paciente_id = 5

        desc = detector._build_description(record)
        assert 'requiere atención' in desc.lower()


class TestKPICalculator:
    """Tests del KPICalculator."""

    def test_dataclass_has_all_required_fields(self):
        """HealthMetrics contiene todos los campos necesarios."""
        from apps.analytics.calculators import HealthMetrics

        missing = [f.name for f in HealthMetrics.__dataclass_fields__.values() if not hasattr(HealthMetrics, f.name)]
        assert not missing



    def test_kpi_calculator_initializes_empty(self):
        """KPICalculator puede instanciarse sin argumentos."""

        from apps.analytics.calculators import KPICalculator

        calc = KPICalculator()
        assert calc is not None