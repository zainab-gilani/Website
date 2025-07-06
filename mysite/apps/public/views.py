from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


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