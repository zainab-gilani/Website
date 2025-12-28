from django.contrib import admin
from django.urls import path, include
from mysite.apps.coursefinder import views as coursefinder_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", coursefinder_views.coursefinder_view, name='home'),
    path("accounts/", include('mysite.apps.accounts.urls')),
    path("coursefinder/", include('mysite.apps.coursefinder.urls'))
]
