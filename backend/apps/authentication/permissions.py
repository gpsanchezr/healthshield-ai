from rest_framework.permissions import BasePermission


class EsAdministrador(BasePermission):
    """Acceso completo al sistema."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'rol', None) == 'administrador'
        )


class EsMedico(BasePermission):
    """Visualización clínica + predicciones."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'rol', None) in ['medico', 'administrador']
        )


class EsAnalista(BasePermission):
    """ETL, analítica y reportes."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'rol', None) in ['analista', 'administrador']
        )

