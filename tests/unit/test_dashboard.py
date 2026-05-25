"""Tests del dashboard y endpoints de analítica visual."""
import pytest

from django.urls import reverse
from rest_framework.test import APIClient

from apps.authentication.models import UsuarioClinico
from apps.etl.models import Paciente, RegistroClinico

pytestmark = pytest.mark.django_db


class TestDashboardCorrelationEndpoint:
    def test_dashboard_correlation_heatmap_for_medico(self):
        user = UsuarioClinico.objects.create_user(
            username='dr_lopez',
            email='dr.lopez@example.com',
            password='medico123',
            rol='medico',
        )
        paciente = Paciente.objects.create(
            id_paciente_original=1,
            nombres='Ana',
            apellidos='Gómez',
            edad=42,
            sexo='F',
        )

        RegistroClinico.objects.bulk_create([
            RegistroClinico(
                paciente=paciente,
                imc=24.5,
                glucosa=98.0,
                presion_sistolica=118,
                presion_diastolica=76,
                colesterol=185.0,
                temperatura=36.7,
                frecuencia_cardiaca=72,
            ),
            RegistroClinico(
                paciente=paciente,
                imc=28.3,
                glucosa=142.0,
                presion_sistolica=132,
                presion_diastolica=84,
                colesterol=210.0,
                temperatura=37.1,
                frecuencia_cardiaca=80,
            ),
        ])

        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse('dashboard_correlation')
        response = client.get(url)

        assert response.status_code == 200
        payload = response.json()
        assert 'labels' in payload
        assert 'matrix' in payload
        assert payload['labels'] and isinstance(payload['matrix'], dict)
        assert 'imc' in payload['matrix']
        assert 'glucosa' in payload['matrix']['imc']
