from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import DashboardView, EcclesiaLoginView

app_name = "core"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("login/", EcclesiaLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
