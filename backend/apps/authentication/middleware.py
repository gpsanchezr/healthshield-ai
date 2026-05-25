import html
import json
import re
from typing import Any
from django.http import QueryDict

class SanitizationMiddleware:
    """
    Middleware de grado industrial para sanitizar inputs.
    Previene inyecciones XSS limpiando tags HTML de POST/PUT/PATCH.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ["POST", "PUT", "PATCH"]:
            # Sanitizar QueryDict
            if isinstance(request.POST, QueryDict):
                request.POST = self._sanitize_querydict(request.POST.copy())

            # Sanitizar JSON (solo si el contenido es JSON)
            if request.content_type and request.content_type.startswith("application/json") and request.body:
                try:
                    data = json.loads(request.body.decode('utf-8'))
                    sanitized_data = self._sanitize_data(data)
                    request._body = json.dumps(sanitized_data, ensure_ascii=False).encode('utf-8')
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

        return self.get_response(request)

    def _sanitize_string(self, value: str) -> str:
        """Limpia etiquetas y scripts maliciosos de un string."""
        if not isinstance(value, str):
            return value

        value = re.sub(r'(?is)<script.*?>.*?</script>', '', value)
        value = re.sub(r'<[^>]+>', '', value)
        value = html.escape(value, quote=True)
        return value.strip()

    def _sanitize_data(self, data: Any) -> Any:
        """Limpia recursivamente estructuras JSON."""
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        if isinstance(data, str):
            return self._sanitize_string(data)
        return data

    def _sanitize_querydict(self, querydict: QueryDict) -> QueryDict:
        """Limpia recursivamente un objeto QueryDict."""
        querydict._mutable = True
        for key in querydict:
            values = querydict.getlist(key)
            sanitized_values = [self._sanitize_string(v) for v in values]
            querydict.setlist(key, sanitized_values)
        querydict._mutable = False
        return querydict
