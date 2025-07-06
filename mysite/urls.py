from django.contrib import admin
from django.urls import path, include


from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include('mysite.apps.public.urls')),
    path("accounts/", include('mysite.apps.accounts.urls')),
]