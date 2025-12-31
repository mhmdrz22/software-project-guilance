from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView
)

def root_view(request):
    return JsonResponse({
        "project": "Team Task Board API",
        "version": "1.0.0",
        "message": "Welcome to the API. Visit /api/docs/ for documentation.",
        "documentation_url": "/api/docs/"
    })

urlpatterns = [
    path("", root_view, name="root"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("tasks.urls")),
    path("api/admin/", include("adminpanel.urls")),

    # OpenAPI schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
