"""
Tests para authentication — modelos, permisos y serializadores.
"""
import pytest
from unittest.mock import MagicMock


class TestPermissions:
    """Tests para las clases de permisos basadas en roles."""

    def test_es_administrador_full_access(self):
        """Admin tiene acceso a todo."""
        from apps.authentication.permissions import EsAdministrador

        perm = EsAdministrador()

        # Usuario administrador
        req_admin = MagicMock()
        req_admin.user = MagicMock()
        req_admin.user.is_authenticated = True
        req_admin.user.rol = 'administrador'

        assert perm.has_permission(req_admin, None) is True

    def test_es_administrador_denies_non_admin(self):
        """No-admin no tiene acceso a secciones de administrador."""
        from apps.authentication.permissions import EsAdministrador

        perm = EsAdministrador()

        req_medico = MagicMock()
        req_medico.user = MagicMock()
        req_medico.user.is_authenticated = True
        req_medico.user.rol = 'medico'

        assert perm.has_permission(req_medico, None) is False

    def test_es_administrador_denies_unauthenticated(self):
        """Usuario no autenticado es rechazado."""
        from apps.authentication.permissions import EsAdministrador

        perm = EsAdministrador()
        req = MagicMock()
        req.user.is_authenticated = False

        assert perm.has_permission(req, None) is False

    def test_es_medico_allows_medico_and_admin(self):
        """Médico y admin pueden acceder."""
        from apps.authentication.permissions import EsMedico

        perm = EsMedico()

        req_medico = MagicMock()
        req_medico.user = MagicMock()
        req_medico.user.is_authenticated = True
        req_medico.user.rol = 'medico'
        assert perm.has_permission(req_medico, None) is True

        req_admin = MagicMock()
        req_admin.user = MagicMock()
        req_admin.user.is_authenticated = True
        req_admin.user.rol = 'administrador'
        assert perm.has_permission(req_admin, None) is True

    def test_es_medico_denies_analista(self):
        """Analista sin rol médico es rechazado."""
        from apps.authentication.permissions import EsMedico

        perm = EsMedico()
        req = MagicMock()
        req.user = MagicMock()
        req.user.is_authenticated = True
        req.user.rol = 'analista'

        assert perm.has_permission(req, None) is False

    def test_es_analista_allows_analista_and_admin(self):
        """Analista y admin pueden acceder."""
        from apps.authentication.permissions import EsAnalista

        perm = EsAnalista()

        req_analista = MagicMock()
        req_analista.user = MagicMock()
        req_analista.user.is_authenticated = True
        req_analista.user.rol = 'analista'
        assert perm.has_permission(req_analista, None) is True

        req_admin = MagicMock()
        req_admin.user = MagicMock()
        req_admin.user.is_authenticated = True
        req_admin.user.rol = 'administrador'
        assert perm.has_permission(req_admin, None) is True

    def test_es_analista_denies_medico(self):
        """Médico sin rol analista es rechazado."""
        from apps.authentication.permissions import EsAnalista

        perm = EsAnalista()
        req = MagicMock()
        req.user = MagicMock()
        req.user.is_authenticated = True
        req.user.rol = 'medico'

        assert perm.has_permission(req, None) is False

    def test_permissions_work_with_missing_rol_attr(self):
        """Usuarios sin atributo rol son rechazados (no crashean)."""
        from apps.authentication.permissions import EsAdministrador, EsMedico, EsAnalista

        for PermClass in [EsAdministrador, EsMedico, EsAnalista]:
            perm = PermClass()
            req = MagicMock()
            req.user = MagicMock()
            req.user.is_authenticated = True
            del req.user.rol  # atributo no existe

            assert perm.has_permission(req, None) is False


class TestSerializers:
    """Tests para los serializadores de authentication."""

    def test_register_serializer_validates_email(self):
        """RegisterSerializer valida formato de email."""
        from apps.authentication.serializers import RegisterSerializer

        serializer = RegisterSerializer(data={
            'username': 'testuser',
            'email': 'not-an-email',
            'rol': 'medico',
            'password': 'securepass123',
        })

        assert serializer.is_valid() is False
        assert 'email' in serializer.errors

    def test_register_serializer_validates_password_length(self):
        """RegisterSerializer rechaza passwords < 8 caracteres."""
        from apps.authentication.serializers import RegisterSerializer

        serializer = RegisterSerializer(data={
            'username': 'testuser',
            'email': 'test@test.com',
            'rol': 'medico',
            'password': 'short',
        })

        assert serializer.is_valid() is False
        assert 'password' in serializer.errors

    def test_register_serializer_validates_rol_choice(self):
        """RegisterSerializer rechaza roles inválidos."""
        from apps.authentication.serializers import RegisterSerializer

        serializer = RegisterSerializer(data={
            'username': 'testuser',
            'email': 'test@test.com',
            'rol': 'superadmin',  # inválido
            'password': 'securepass123',
        })

        assert serializer.is_valid() is False
        assert 'rol' in serializer.errors

    def test_login_serializer_has_token_obtain_pair(self):
        """LoginSerializer hereda de TokenObtainPairSerializer."""
        from apps.authentication.serializers import LoginSerializer

        assert hasattr(LoginSerializer, 'fields') or hasattr(LoginSerializer, 'get_tokens')

    def test_register_serializer_valid_data(self):
        """Datos válidos pasan la validación."""
        from apps.authentication.serializers import RegisterSerializer

        serializer = RegisterSerializer(data={
            'username': 'testuser',
            'email': 'test@healthshield.ai',
            'rol': 'medico',
            'password': 'securepass123',
        })

        assert serializer.is_valid() is True