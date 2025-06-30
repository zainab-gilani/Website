from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


def index(request)-> HttpResponse:
    print(request.user)
    return render(request, "index.html")
# enddef


def about(request)-> HttpResponse:
    return render(request, "about.html")
# enddef


def contact(request)-> HttpResponse:
    return render(request, "contact.html")
# enddef


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"
#endclass