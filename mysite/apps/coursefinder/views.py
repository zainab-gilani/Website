from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

# Create your views here.

@login_required
def coursefinder_view(request):
    return render(request, 'coursefinder/course_finder.html', {"mode": "user"})
#enddef

def guest_coursefinder_view(request):
    return render(request, 'coursefinder/course_finder.html')
#enddef