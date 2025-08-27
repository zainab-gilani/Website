from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from .views import resend_activation_view, saved_matches_view, CustomLoginView
from .forms import CustomLoginForm

from django.contrib.auth.views import LogoutView

app_name = "accounts"

urlpatterns = [
    path("signup/", views.register_view, name="signup"),
    # Django Auth
    path(
        "login/",
        CustomLoginView.as_view(
            authentication_form=CustomLoginForm
        ),
        name="login",
    ),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('resend-activation/', resend_activation_view, name='resend_activation'),
    path("profile/", views.profile_view, name="profile"),
    path('saved-matches/', saved_matches_view, name="saved_matches"),
    path('save-match/', views.save_match, name='save_match'),
]