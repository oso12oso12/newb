from django.urls import path
from . import views

app_name = "bank"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("accounts/", views.AccountsView.as_view(), name="accounts"),
    path("transfer/", views.TransferView.as_view(), name="transfer"),
    path("deposit/", views.DepositView.as_view(), name="deposit"),
    path("help-center/", views.HelpCenterView.as_view(), name="help_center"),
    path("settings/", views.SettingsView.as_view(), name="settings_page"),
    path("settings/toggle/", views.SettingsToggleView.as_view(), name="settings_toggle"),
]
