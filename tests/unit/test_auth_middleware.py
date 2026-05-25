"""Tests para la middleware de sanitización de inputs."""

import json
from django.http import HttpRequest, QueryDict

from apps.authentication.middleware import SanitizationMiddleware


def test_sanitization_middleware_cleans_querydict_post_data():
    request = HttpRequest()
    request.method = 'POST'
    request.content_type = 'application/x-www-form-urlencoded'
    request.POST = QueryDict('name=<script>alert(1)</script>Juan&bio=<b>Hola</b>')
    request._body = b''

    middleware = SanitizationMiddleware(lambda req: req)
    middleware(request)

    assert request.POST['name'] == 'Juan'
    assert request.POST['bio'] == 'Hola'


def test_sanitization_middleware_cleans_json_body():
    request = HttpRequest()
    request.method = 'POST'
    request.content_type = 'application/json'
    request._body = json.dumps({
        'message': '<script>alert("xss")</script>Bienvenido',
        'details': ['<b>fuerte</b>', '<img src=x onerror=alert(1)>'],
    }).encode('utf-8')
    request.body  # ensure property access does not break middleware

    middleware = SanitizationMiddleware(lambda req: req)
    middleware(request)

    body = json.loads(request._body.decode('utf-8'))
    assert body['message'] == 'Bienvenido'
    assert body['details'][0] == 'fuerte'
    assert body['details'][1] == ''


def test_sanitize_string_preserves_plain_text():
    middleware = SanitizationMiddleware(lambda req: req)
    assert middleware._sanitize_string('texto normal') == 'texto normal'
    assert middleware._sanitize_string('  <p>test</p>  ') == 'test'
