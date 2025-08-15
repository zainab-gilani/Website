from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .types import UniMatchResult
# Create your views here.

@login_required
def coursefinder_view(request):
    return render(request, 'coursefinder/course_finder.html', {"mode": "user"})
#enddef

def guest_coursefinder_view(request):
    return render(request, 'coursefinder/course_finder.html')
#enddef

def get_dummy_matches():
    fake_unis = [
        UniMatchResult("University of Exampleton", "Computer Science BSc", "A in Maths, B in Physics",
                       "https://example.com/cs"),
        UniMatchResult("Fakeham Uni", "Mechanical Engineering MEng", "A in Physics, B in Maths",
                       "https://fakeham.ac.uk/eng"),
        UniMatchResult("Demo Institute", "Software Engineering BSc", "B in Maths, B in Computing",
                       "https://demo.edu/se"),
    ]

    return fake_unis
#enddef

def course_search_view(request):
    if request.method == "POST":
        query = request.POST.get('query', '')

        if query:
            parsed_input = "Parsed grades: A in Maths, B in Physics"
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