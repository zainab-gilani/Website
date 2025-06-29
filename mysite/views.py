from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render

def index(request):
    return render(request, 'index.html')
#enddef

def about(request):
    return render(request, 'about.html')
#enddef

def contact(request):
    return render(request, 'contact.html')
#enddef