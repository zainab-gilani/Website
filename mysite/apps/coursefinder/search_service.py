"""
Search service that uses NLP parser to find matching courses
"""
from typing import List, Dict, Any

from django.db.models import Q

from mysite.apps.nlp.course_interests import parse_interests
from mysite.apps.nlp.grade_parser import GradeParser
from .models import Course
from .types import UniMatchResult
from .university_search import expand_query_with_synonyms


def search_courses(query: str, filters: Dict) -> Dict[str, Any]:
    """
    Main search function that parses natural language and finds matching courses.

    :param query: Natural language input from user describing grades and interests
    :param filters: Dictionary containing filter options (course_type, duration, mode, location, etc.)
    :return: Dictionary containing query, parsed_grades, interests, ucas_points, and matching_courses list
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
    # endif

    # find matching courses
    # Pass filters dictionary to the next function
    courses = find_matching_courses(
        grades=result["parsed_grades"],
        ucas_points=ucas_points,
        interests=result["interests"],
        filters=filters
    )

    result["matching_courses"] = courses

    return result


# enddef


def calculate_ucas_points(grades: Dict[str, str]) -> int:
    """
    Calculates total UCAS points from grades dictionary.

    :param grades: Dictionary mapping subject names to grade strings (e.g., {"mathematics": "A", "physics": "B"})
    :return: Total UCAS points as integer
    """
    # UCAS points for each grade
    grade_points = {
        'A*': 56,
        'A': 48,
        'B': 40,
        'C': 32,
        'D': 24,
        'E': 16,
        'U': 0,
        'D*': 56,
        'M': 32,
        'P': 16
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


def find_matching_courses(grades: Dict, ucas_points: int, interests: List[str], filters: Dict) -> List:
    """
    Finds courses that match the given criteria by comparing grades and interests with database entries.

    :param grades: Dictionary of subject-grade pairs
    :param ucas_points: Total UCAS points calculated from grades
    :param interests: List of course/subject names the user is interested in
    :param filters: Dictionary containing filter options (course_type, duration, mode, location, etc.)
    :return: List of UniMatchResult objects containing matching courses
    """
    results = []

    # need to find courses the student can actually get into with their grades
    if ucas_points > 0:
        # grab all the courses from database
        all_courses = Course.objects.select_related('university').prefetch_related('entryrequirement')

        # if they mentioned interests, look for those courses first
        if interests:
            interest_query = Q()
            for interest in interests:
                # use the synonym function to expand search terms
                # this means if someone searches "math" it also finds "mathematics"
                expanded_terms = expand_query_with_synonyms(interest)
                for term in expanded_terms:
                    interest_query |= Q(name__icontains=term)
                # endfor
            # endfor
            all_courses = all_courses.filter(interest_query)
        # endif

        # get courses where they have enough points or no requirements
        qualifying_courses = all_courses.filter(
            Q(entryrequirement__min_ucas_points__lte=ucas_points) | Q(entryrequirement__isnull=True)
        )

    elif interests:
        # they didn't give grades but mentioned interests
        interest_query = Q()
        for interest in interests:
            # use the synonym function to expand search terms
            # this means if someone searches "math" it also finds "mathematics"
            expanded_terms = expand_query_with_synonyms(interest)
            for term in expanded_terms:
                interest_query |= Q(name__icontains=term)
            # endfor
        # endfor
        qualifying_courses = Course.objects.select_related('university').prefetch_related('entryrequirement').filter(
            interest_query)
    else:
        # nothing to search for
        qualifying_courses = Course.objects.none()
    # endif

    # apply ucas points filter if selected
    if filters.get('ucas_range'):
        try:
            min_points = int(filters['ucas_range'])
            # only show courses that require at least this many points
            if min_points > 0:
                qualifying_courses = qualifying_courses.filter(
                    entryrequirement__min_ucas_points__gte=min_points
                )
            # endif
        except ValueError:
            pass
        # endtry
    # endif

    # filter by course type if they selected one
    if filters.get('course_type'):
        selected_type = filters['course_type']
        # matches "BA (Hons)" in both short and long forms
        qualifying_courses = qualifying_courses.filter(course_type__icontains=selected_type)
    # endif

    if filters.get('duration'):
        selected_duration = filters['duration']
        if "5+" in selected_duration:
            # match courses with 5, 6, or 7 years
            qualifying_courses = qualifying_courses.filter(
                Q(duration__icontains="5 year") | Q(duration__icontains="6 year") | Q(duration__icontains="7 year")
            )
        else:
            # extract the number and match with the word "year" to avoid matching months
            years = selected_duration.split(' ')[0]
            qualifying_courses = qualifying_courses.filter(duration__icontains=years + " year")
        # endif
    # endif

    if filters.get('mode'):
        qualifying_courses = qualifying_courses.filter(mode__icontains=filters['mode'])
    # endif

    if filters.get('location'):
        selected_region = filters['location']
        region_map = filters.get('region_mapping', {})

        cities_in_region = region_map.get(selected_region, [])

        if cities_in_region:
            location_query = Q()
            for city in cities_in_region:
                location_query |= Q(location__icontains=city)
            # endfor
            qualifying_courses = qualifying_courses.filter(
                Q(location__in=cities_in_region) |
                Q(university__location__in=cities_in_region) |
                location_query
            )
        # endif
    # endif

    # if user wants to see only courses with grade requirements
    if filters.get('only_grades'):
        # filter for courses that have requirements and grades aren't empty
        qualifying_courses = qualifying_courses.filter(
            entryrequirement__has_requirements=True,
            entryrequirement__display_grades__isnull=False
        ).exclude(
            entryrequirement__display_grades=''
        ).distinct()
    # endif

    # if user wants to see only courses with no requirements
    if filters.get('no_requirements'):
        # filter for courses where has_requirements is false
        qualifying_courses = qualifying_courses.filter(
            entryrequirement__has_requirements=False
        ).distinct()
    # endif

    courses_to_show = list(qualifying_courses[:20])

    # format the courses as UniMatchResult objects for the template
    for course in courses_to_show:
        try:
            req = course.entryrequirement
            # decide what to show for requirements
            if req.has_requirements:
                # course has requirements so show them
                if req.display_grades and req.display_grades.strip():
                    requirements_str = req.display_grades
                elif req.min_ucas_points > 0:
                    requirements_str = f"{req.min_ucas_points} UCAS points"
                else:
                    requirements_str = "No specific requirements"
                # endif

                # add btec grades if they exist
                if req.btec_grades:
                    requirements_str += f" / {req.btec_grades}"
                # endif
            else:
                # no requirements for this course
                requirements_str = "No specific requirements"
            # endif
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
