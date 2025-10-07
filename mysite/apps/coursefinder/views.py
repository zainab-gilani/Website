from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse
from .types import UniMatchResult
from .search_service import search_courses
from .university_search import search_universities
from ..accounts.models import SavedMatch


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

def mark_saved_matches(results, user):
    # Only check saved matches if user is logged in
    if not user.is_authenticated:
        return results
    #endif
    
    # Get all saved matches for this user
    saved_matches = SavedMatch.objects.filter(user=user)
    
    # Check each result to see if it's been saved
    for result in results:
        result.is_saved = False  # Default to not saved
        
        # Look through saved matches to see if this one is saved
        for saved_match in saved_matches:
            # Check if all the details match
            if (result.university == saved_match.university and 
                result.course == saved_match.course and 
                result.course_type == saved_match.course_type and
                result.duration == saved_match.duration and
                result.requirements == saved_match.requirements and
                result.course_link == saved_match.course_link):
                result.is_saved = True
                break  # Found a match, no need to keep looking
            #endif
        #endfor
    #endfor
    
    return results
#enddef

def coursefinder_view(request):
    tab = request.GET.get('tab') or request.POST.get('tab') or "matches"
    results = []
    parsed_input = ""
    query = ""
    
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Tab: {tab}")
    print(f"DEBUG: User authenticated: {request.user.is_authenticated}")

    if request.method == 'POST':
        query = request.POST.get('query', '')
        print(f"DEBUG: Query received: '{query}'")
        
        if tab == 'matches':
            # this tab uses the nlp parser to work out what grades they have
            if query:
                # run the search with nlp parsing
                search_result = search_courses(query)
                results = search_result["matching_courses"]
                print(f"DEBUG: Found {len(results)} results from search_courses")
                # Mark which results are saved for logged in users
                results = mark_saved_matches(results, request.user)
                print(f"DEBUG: After marking saved matches: {len(results)} results")
                
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
                results = search_universities(query)
                print(f"DEBUG: Found {len(results)} results from search_universities")
                # Mark which results are saved for logged in users
                results = mark_saved_matches(results, request.user)
                print(f"DEBUG: After marking saved matches: {len(results)} results")
                if results:
                    parsed_input = f"Found {len(results)} results for '{query}'"
                else:
                    parsed_input = f"No universities or courses found for '{query}'"
                #endif
            #endif
        #endif
    #endif

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        print(f"DEBUG: AJAX request - results count: {len(results)}")
        # ajax request so return just the html for the results
        # put the message and table together
        if parsed_input:
            message_html = f'<p style="text-align:center; margin-top:30px; font-size:1.3rem; font-weight:700; color:#2D5289FF;">{parsed_input}</p>'
        else:
            message_html = ''
        #endif
        
        table_html = render_to_string(
            'coursefinder/_results_table.html', {
                'results': results,
                'user': request.user,  # Add user context for authentication checks
            }, request=request
        )
        print(f"DEBUG: Rendered table_html length: {len(table_html)}")
        
        # stick them together
        full_html = message_html + table_html
        
        return JsonResponse({
            'table_html': full_html,
            'parsed_input': parsed_input
        })
    #endif

    print(f"DEBUG: Final results count: {len(results)}")
    print(f"DEBUG: Final parsed_input: '{parsed_input}'")
    
    return render(request, 'coursefinder/course_finder.html', {
        "mode": tab,
        'results': results,
        'parsed_input': parsed_input,
        'query': query,
    })
#enddef