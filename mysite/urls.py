from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include('mysite.apps.public.urls')),
    path("accounts/", include('mysite.apps.accounts.urls')),
    path("coursefinder/", include('mysite.apps.coursefinder.urls')),
]