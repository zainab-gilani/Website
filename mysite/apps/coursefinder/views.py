from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .types import UniMatchResult
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

# Create your views here.

@login_required
def coursefinder_view(request):
    return render(request, 'coursefinder/course_finder.html', {"mode": "user"})
#enddef

def guest_coursefinder_view(request):
    return render(request, 'coursefinder/course_finder.html')
#enddef

from django.shortcuts import render, redirect


def get_dummy_matches():
    fake_unis = [
        UniMatchResult(
            "University of Exampleton", "Computer Science", "BSc (Hons)", "3 years",
            "A*AA–AAB", "https://example.com/cs"
        ),
        UniMatchResult(
            "Fakeham Uni", "Mechanical Engineering", "MEng", "4 years",
            "A in Physics, B in Maths", "https://fakeham.ac.uk/eng"
        ),
        UniMatchResult(
            "Demo Institute", "Software Engineering", "BSc (Hons)", "3 years",
            "B in Maths, B in Computing", "https://demo.edu/se"
        ),
    ]
    return fake_unis
#enddef

def course_search_view(request):
    if request.method == "POST":
        query = request.POST.get('query', '')

        if query:
            parsed_input = "The following universities accept: A in Maths, B in Physics"
            matches = get_dummy_matches()
        else:
            parsed_input = ""
            matches = []
        #endif

        return render(request, 'coursefinder/course_finder.html', {
            'query': query,
            'parsed_input': parsed_input,
            'results': matches
        })
    #endif

    return render(request, 'coursefinder/course_finder.html')
#endif