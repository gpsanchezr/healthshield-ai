from django.urls import path

from .views import DashboardSummaryView, DashboardCorrelationView, dashboard_home_view

urlpatterns = [
    # HTML page (template): frontend/templates/dashboard/index.html
    path('dashboard/', dashboard_home_view, name='dashboard_home'),

    # JSON API for the dashboard charts
    path('api/dashboard/', DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('api/dashboard/correlacion/', DashboardCorrelationView.as_view(), name='dashboard_correlation'),
]

