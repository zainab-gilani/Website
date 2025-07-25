from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from .views import resend_activation_view
from .forms import CustomLoginForm

from django.contrib.auth.views import LogoutView

app_name = "accounts"

urlpatterns = [
    path("signup/", views.register_view, name="signup"),
    path("profile", views.ProfileView.as_view(), name="profile"),
    # Django Auth
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=CustomLoginForm
        ),
        name="login",
    ),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('resend-activation/', resend_activation_view, name='resend_activation'),
]