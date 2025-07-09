from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

from .forms import CustomUserCreationForm


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"
#endclass

def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("accounts:login")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", { "form": form })
#enddef