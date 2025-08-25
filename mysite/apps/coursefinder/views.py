from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse
from .types import UniMatchResult


# Create your views here.

def guest_coursefinder_view(request):
    return render(request, 'coursefinder/course_finder.html')
#enddef

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

def coursefinder_view(request):
    tab = request.GET.get('tab') or request.POST.get('tab') or "matches"
    results = []
    parsed_input = ""
    query = ""

    if request.method == 'POST':
        query = request.POST.get('query', '')
        if tab == 'matches':
            if query:
                parsed_input = "The following universities accept: A in Maths, B in Physics"
                results = get_dummy_matches()
            #endif
        elif tab == 'search':
            pass
        #endif
    #endif

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        table_html = render_to_string(
            'coursefinder/_results_table.html', {
                'results': results,
            }, request=request
        )
        return JsonResponse({'table_html': table_html})
    #endif

    return render(request, 'coursefinder/course_finder.html', {
        "mode": tab,
        'results': results,
        'parsed_input': parsed_input,
        'query': query,
    })
#enddef