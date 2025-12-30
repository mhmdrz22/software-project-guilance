from django.urls import path
from .views import AdminOverviewView, AdminNotifyView

urlpatterns = [
    path("overview/", AdminOverviewView.as_view(), name="admin-overview"),
    path("notify/", AdminNotifyView.as_view(), name="admin-notify"),
]
