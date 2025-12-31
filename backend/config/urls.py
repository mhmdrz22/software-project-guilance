from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView
)

def home_view(request):
    return JsonResponse({
        "message": "Welcome to Task Board API - Software Engineering Project",
        "version": "1.0.0",
        "endpoints": {
            "authentication": "/api/auth/",
            "tasks": "/api/tasks/",
            "admin_panel": "/api/admin/",
            "admin_dashboard": "/admin/",
            "api_docs": "/api/docs/",
            "api_schema": "/api/schema/",
        },
        "status": "running"
    })

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/tasks/', include('tasks.urls')),
    path('api/admin/', include('adminpanel.urls')),
    # OpenAPI schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
