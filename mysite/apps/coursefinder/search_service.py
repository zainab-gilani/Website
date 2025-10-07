"""
Search service that uses NLP parser to find matching courses
"""
from typing import List, Dict, Any
from django.db.models import Q
from .models import University, Course, EntryRequirement, SubjectRequirement
from mysite.apps.nlp.grade_parser import GradeParser
from mysite.apps.nlp.course_interests import parse_interests


def search_courses(query: str) -> Dict[str, Any]:
    """
    Main search function that parses natural language and finds matching courses.

    Examples:
    - "I got AAB in Maths, Physics, Chemistry"
    - "Looking for Computer Science courses"
    - "BBB grades, interested in Law"
    """

    # initialize parser
    parser = GradeParser()

    # get both grades and interests from the input
    parsed = parser.parse(query)

    # double check for course interests using the other parser too
    interests_result = parse_interests(query)

    # put all the interests together from both parsers
    all_interests = parsed.get("interests", [])
    if interests_result and "interests" in interests_result:
        for interest in interests_result["interests"]:
            if interest not in all_interests:
                all_interests.append(interest)

    # make the response dictionary with what we found
    result = {
        "query": query,
        "parsed_grades": parsed.get("grades", {}),
        "interests": all_interests,
        "dropped": [],  # Could extract this from parsed data if needed
        "matching_courses": []
    }

    # calculate UCAS points from grades
    ucas_points = 0
    if result["parsed_grades"]:
        ucas_points = calculate_ucas_points(result["parsed_grades"])
        result["ucas_points"] = ucas_points

    # find matching courses
    courses = find_matching_courses(
        grades=result["parsed_grades"],
        ucas_points=ucas_points,
        interests=result["interests"]
    )

    result["matching_courses"] = courses

    return result
# enddef


def calculate_ucas_points(grades: Dict[str, str]) -> int:
    """
    Calculate total UCAS points from grades dict.
    """
    # UCAS points for each grade
    grade_points = {
        'A*': 56,
        'A': 48,
        'B': 40,
        'C': 32,
        'D': 24,
        'E': 16,
        'U': 0
    }

    total = 0
    for subject, grade in grades.items():
        grade = grade.upper()
        if grade in grade_points:
            total += grade_points[grade]
        # endif
    # endfor

    return total
# enddef


def find_matching_courses(grades: Dict, ucas_points: int, interests: List[str]) -> List:
    """
    Find courses that match the given criteria.
    This is for the MATCHES tab - focuses on finding courses that accept the student's grades.
    Returns course data formatted for the template.
    """
    from .types import UniMatchResult

    results = []

    # need to find courses the student can actually get into with their grades
    if ucas_points > 0:
        # grab all the courses from database
        all_courses = Course.objects.select_related('university').prefetch_related('entryrequirement')

        # if they mentioned interests, look for those courses first
        if interests:
            interest_query = Q()
            for interest in interests:
                interest_query |= Q(name__icontains=interest)
            # endfor
            all_courses = all_courses.filter(interest_query)
        # endif

        # find courses where student has enough points OR no requirements listed
        # this filters in the database which is way faster
        qualifying_courses = all_courses.filter(
            Q(entryrequirement__min_ucas_points__lte=ucas_points) | Q(entryrequirement__isnull=True)
        )[:20]

        # convert to list for processing
        courses_to_show = list(qualifying_courses)

    elif interests:
        # they didn't give grades but mentioned interests
        interest_query = Q()
        for interest in interests:
            interest_query |= Q(name__icontains=interest)
        # endfor
        courses_to_show = Course.objects.select_related('university').prefetch_related('entryrequirement').filter(interest_query)[:20]
    else:
        # nothing to search for
        courses_to_show = []
    # endif

    # format results as UniMatchResult objects for the template
    for course in courses_to_show:
        try:
            req = course.entryrequirement
            requirements_str = req.display_grades or f"{req.min_ucas_points} UCAS points"
            if req.btec_grades:
                requirements_str += f" / {req.btec_grades}"
            #endif
        except:
            requirements_str = "No specific requirements"
        # endtry

        match = UniMatchResult(
            university=course.university.name,
            course=course.name,
            course_type=course.course_type,
            duration=course.duration,
            requirements=requirements_str,
            course_link=course.link or "#"
        )
        results.append(match)
    # endfor

    return results
# enddef