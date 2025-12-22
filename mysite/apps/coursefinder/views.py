from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse
from .types import UniMatchResult
from .search_service import search_courses
from .university_search import search_universities
from ..accounts.models import SavedMatch
from .models import Course


# Create your views here.

UCAS_OPTIONS = [
    (48, "48+ (Pass/PPP)"),
    (80, "80+ (BCC/BBC)"),
    (96, "96+ (CCC/BCC)"),
    (104, "104+ (BCC/CDD)"),
    (112, "112+ (BBC)"),
    (120, "120+ (BBB)"),
    (128, "128+ (ABB)"),
    (136, "136+ (AAB)"),
    (144, "144+ (AAA)"),
    (168, "168+ (A*A*A*)"),
]

DURATION_OPTIONS = [
    "1 Year",
    "2 Years",
    "3 Years",
    "4 Years",
    "5+ Years",
]

MODE_OPTIONS = [
"Full-time",
    "Part-time",
    "Sandwich", # e.g. "Placement year", "Industry", etc.
    "Distance Learning"
]

LOCATION_REGIONS = {
    "London & South East": ["London", "Brighton", "Oxford", "Reading", "Southampton", "Surrey", "Kent", "Sussex"],
    "South West": ["Bristol", "Bath", "Exeter", "Plymouth", "Bournemouth", "Falmouth"],
    "West Midlands": ["Birmingham", "Coventry", "Warwick", "Wolverhampton", "Aston"],
    "East Midlands": ["Nottingham", "Leicester", "Loughborough", "Derby", "Lincoln"],
    "North West": ["Manchester", "Liverpool", "Lancaster", "Chester", "Salford"],
    "North East & Yorkshire": ["Leeds", "Sheffield", "York", "Newcastle", "Durham", "Hull", "Bradford"],
    "Scotland": ["Edinburgh", "Glasgow", "Aberdeen", "St Andrews", "Dundee", "Stirling"],
    "Wales": ["Cardiff", "Swansea", "Bangor", "Aberystwyth"],
    "Northern Ireland": ["Belfast", "Ulster"],
}

LOCATION_OPTIONS = list(LOCATION_REGIONS.keys())

COURSE_TYPE_OPTIONS = [
    "BA (Hons)",  # bachelor of arts with honours
    "BSc (Hons)",  # bachelor of science with honours
    "BEng (Hon)",  # bachelor of engineering with honours
    "LLB (Hons)",  # bachelor of law with honours
    "MA",  # master of arts
    "MSc",  # master of science
    "MBA",  # master of business administration
    "MEng",  # integrated masters in engineering
    "Foundation",  # foundation degrees (FdA, FdSc, etc)
]

def guest_coursefinder_view(request):
    """
    Renders the course finder page for guest users.

    :param request: Django HTTP request object
    :return: Rendered HTML response for course finder page
    """
    # pass filter options to template
    context = {
        'course_types': COURSE_TYPE_OPTIONS,
        'durations': DURATION_OPTIONS,
        'modes': MODE_OPTIONS,
        'locations': LOCATION_OPTIONS,
        'ucas_options': UCAS_OPTIONS,
    }
    return render(request, 'coursefinder/course_finder.html', context)
#enddef

def resources_view(request):
    return render(request, 'coursefinder/resources.html')
#enddef

def get_dummy_matches():
    """
    Creates example university match results for testing purposes.

    :return: List of dummy UniMatchResult objects
    """
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

def mark_saved_matches(results, user):
    """
    Marks which course results have been saved by the user.

    :param results: List of course result objects to check
    :param user: Django user object (must be authenticated)
    :return: List of results with is_saved attribute added
    """
    # Only check saved matches if user is logged in
    if not user.is_authenticated:
        return results
    #endif

    # Get all the courses this user has saved
    saved_matches = SavedMatch.objects.filter(user=user)

    # Go through each course result and check if it's been saved
    for result in results:
        result.is_saved = False  # Start by assuming it's not saved

        # Check if this result matches any of the saved courses
        for saved_match in saved_matches:
            # We check university name, course name, and link to see if they match
            if (result.university == saved_match.university and
                result.course == saved_match.course and
                result.course_link == saved_match.course_link):
                result.is_saved = True
                break  # We found it, so stop looking
            #endif
        #endfor
    #endfor

    return results
#enddef

def coursefinder_view(request):
    """
    Main view for course finder page that handles both matches and search tabs.

    :param request: Django HTTP request object
    :return: Rendered HTML response or JSON response for AJAX requests
    """
    tab = request.GET.get('tab') or request.POST.get('tab') or "matches"
    results = []
    parsed_input = ""
    query = ""
    #
    # print(f"DEBUG: Request method: {request.method}")
    # print(f"DEBUG: Tab: {tab}")
    # print(f"DEBUG: User authenticated: {request.user.is_authenticated}")

    if request.method == 'POST':
        query = request.POST.get('query', '')
        # print(f"DEBUG: Query received: '{query}'")

        filters = {
            'course_type': request.POST.get('course_type', ''),
            'duration': request.POST.get('duration', ''),
            'mode': request.POST.get('mode', ''),
            'location': request.POST.get('location', ''),
            'only_grades': request.POST.get('only_grades', '') == 'on',
            'no_requirements': request.POST.get('no_requirements', '') == 'on',
            'ucas_range': request.POST.get('ucas_range', '')
        }

        filters['region_mapping'] = LOCATION_REGIONS


        if tab == 'matches':
            # this tab uses the nlp parser to work out what grades they have
            if query:
                # run the search with nlp parsing
                search_result = search_courses(query, filters)
                results = search_result["matching_courses"]
                # print(f"DEBUG: Found {len(results)} results from search_courses")
                # Mark which results are saved for logged-in users
                results = mark_saved_matches(results, request.user)
                # print(f"DEBUG: After marking saved matches: {len(results)} results")
                
                # make a message showing what we understood from their input
                grades_text = ""
                if search_result["parsed_grades"]:
                    grade_items = []
                    for subject, grade in search_result["parsed_grades"].items():
                        grade_items.append(f"{grade} in {subject.title()}")
                    #endfor
                    grades_text = ", ".join(grade_items)
                #endif
                
                interests_text = ""
                if search_result["interests"]:
                    interests_text = ", ".join([i.title() for i in search_result["interests"]])
                #endif
                
                # different messages depending on what we found
                if grades_text and interests_text:
                    if results:
                        parsed_input = f"Found {len(results)} courses accepting: {grades_text} • Interests: {interests_text}"
                    else:
                        parsed_input = f"No courses found accepting: {grades_text} with interests in {interests_text}"
                    #endif
                elif grades_text:
                    if results:
                        ucas = search_result.get("ucas_points", 0)
                        parsed_input = f"Found {len(results)} courses accepting: {grades_text} ({ucas} UCAS points)"
                    else:
                        parsed_input = f"No courses found for: {grades_text}"
                    #endif
                elif interests_text:
                    if results:
                        parsed_input = f"Found {len(results)} courses in: {interests_text}"
                    else:
                        parsed_input = f"No courses found for: {interests_text}"
                    #endif
                else:
                    parsed_input = f"Could not parse grades or interests from: {query}"
                #endif
            #endif
            
        elif tab == 'search':
            # this tab is just basic search without nlp
            if query:
                results = search_universities(query, filters)
                # print(f"DEBUG: Found {len(results)} results from search_universities")
                # Mark which results are saved for logged in users
                results = mark_saved_matches(results, request.user)
                # print(f"DEBUG: After marking saved matches: {len(results)} results")
                if results:
                    parsed_input = f"Found {len(results)} results for '{query}'"
                else:
                    parsed_input = f"No universities or courses found for '{query}'"
                #endif
            #endif
        #endif
    #endif

    # This context will now pass all filter options to the template
    context = {
        "mode": tab,
        'results': results,
        'parsed_input': parsed_input,
        'query': query,
        'course_types': COURSE_TYPE_OPTIONS,
        'durations': DURATION_OPTIONS,
        'modes': MODE_OPTIONS,
        'locations': LOCATION_OPTIONS,
        'ucas_options': UCAS_OPTIONS,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # print(f"DEBUG: AJAX request - results count: {len(results)}")
        # ajax request so return just the html for the results
        # put the message and table together
        if parsed_input:
            message_html = f'<p style="text-align:center; margin-top:30px; font-size:1.3rem; font-weight:700; color:#2D5289FF;">{parsed_input}</p>'
        else:
            message_html = ''
        #endif

        # Pass the full context to the template
        table_html = render_to_string(
            'coursefinder/_results_table.html',
            context,
            request=request
        )
        # print(f"DEBUG: Rendered table_html length: {len(table_html)}")

        # stick them together
        full_html = message_html + table_html

        return JsonResponse({
            'table_html': full_html,
            'parsed_input': parsed_input
        })
    #endif
    #
    # print(f"DEBUG: Final results count: {len(results)}")
    # print(f"DEBUG: Final parsed_input: '{parsed_input}'")
    
    return render(request, 'coursefinder/course_finder.html', context)
#enddef