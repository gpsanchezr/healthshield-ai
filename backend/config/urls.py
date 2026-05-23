from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.http import HttpResponse
from django.views.generic import RedirectView


def alertas_view(request):
    from django.template.loader import get_template

    template = get_template('alertas/index.html')
    return HttpResponse(template.render({}, request))


def simulacion_view(request):
    from django.template.loader import get_template

    template = get_template('simulation/index.html')
    return HttpResponse(template.render({}, request))


urlpatterns = [
    path('', RedirectView.as_view(url='/admin/'), name='root_redirect'),

    # Admin
    path('admin/', admin.site.urls),

    # ── Template Pages ────────────────────────────────────────────────────────
    path('alertas/', alertas_view, name='alertas'),
    path('simulador/', simulacion_view, name='simulador'),

    # ── API Routes ────────────────────────────────────────────────────────────
    path('api/', include('apps.authentication.urls')),
    path('api/', include('apps.etl.urls')),
    path('api/', include('apps.ml.urls')),
    path('api/', include('apps.analytics.urls')),
    path('', include('apps.dashboard.urls')),

    path('api/', include('apps.reports.urls')),

    # ── OpenAPI / Swagger ─────────────────────────────────────────────────────
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

