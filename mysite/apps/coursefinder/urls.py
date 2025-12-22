from django.urls import path
from . import views

app_name = 'coursefinder'

urlpatterns = [
    path('', views.coursefinder_view, name='coursefinder'),
    path('guest/', views.guest_coursefinder_view, name='guest_coursefinder'),
    path('search/', views.coursefinder_view, name='course_search'),
    path('resources/', views.resources_view, name='resources'),
]