"""
University search service for general text-based searching
"""
from typing import List
from django.db.models import Q
from .models import University, Course
from .types import UniMatchResult
from ..nlp.synonyms import SYNONYMS


def expand_query_with_synonyms(query: str) -> List[str]:
    """
    Converts query to main subject name if it's a synonym.

    :param query: Search query string from user
    :return: List containing main subject name or original query in lowercase
    """
    if not query:
        return []
    # endif

    query_lower = query.strip().lower()

    # get course synonyms
    courses = SYNONYMS.get('courses', {})

    # see if query matches any synonym
    for subject, synonym_list in courses.items():
        for synonym in synonym_list:
            if synonym.lower() == query_lower:
                # found a match so return the main subject
                return [subject.lower()]
            # endif
        # endfor
    # endfor

    # no synonym found so just return original query
    return [query_lower]


# enddef


def search_universities(query: str, filters: dict = None) -> List:
    """
    Searches for universities and courses based on general text query.

    :param query: Search string (university name, location, or course name)
    :param filters: Optional dictionary containing filter options (course_type, duration, mode, location)
    :return: List of UniMatchResult objects containing matching courses
    """

    if not query:
        return []
    # endif

    if filters is None:
        filters = {}
    # endif

    # get search terms with synonyms
    search_terms = expand_query_with_synonyms(query)

    results = []

    # build the search query
    course_query = Q()
    for term in search_terms:
        # search in course name, uni name, and location
        term_query = Q(name__icontains=term) | Q(university__name__icontains=term) | Q(
            university__location__icontains=term)
        course_query |= term_query
    # endfor

    courses = Course.objects.select_related('university', 'entryrequirement').filter(course_query)

    # filter by course type if selected
    if filters.get('course_type'):
        selected_type = filters['course_type']
        # matches "BA (Hons)" in both short and long forms
        courses = courses.filter(course_type__icontains=selected_type)
    # endif

    # filter by duration
    if filters.get('duration'):
        val = filters['duration']
        if "5+" in val:
            # match courses with 5, 6, or 7 years
            courses = courses.filter(
                Q(duration__icontains="5 year") | Q(duration__icontains="6 year") | Q(duration__icontains="7 year"))
        else:
            # extract the number and match with the word "year" to avoid matching months
            years = val.split(' ')[0]
            courses = courses.filter(duration__icontains=years + " year")
        # endif
    # endif

    # filter by mode
    if filters.get('mode'):
        courses = courses.filter(mode__icontains=filters['mode'])
    # endif

    # filter by location/region
    if filters.get('location'):
        region = filters['location']
        region_map = filters.get('region_mapping', {})
        cities = region_map.get(region, [])

        if cities:
            loc_q = Q()
            for city in cities:
                loc_q |= Q(university__location__icontains=city) | Q(location__icontains=city)
            # endfor
            courses = courses.filter(loc_q)
        # endif
    # endif

    # filter by ucas points
    if filters.get('ucas_range'):
        try:
            min_points = int(filters['ucas_range'])
            if min_points > 0:
                courses = courses.filter(entryrequirement__min_ucas_points__lte=min_points)
            # endif
        except ValueError:
            pass
        # endtry
    # endif

    if filters.get('only_grades') and filters.get('no_requirements'):
        filters['no_requirements'] = False
    # endif

    # if user wants to see only courses with grade requirements
    if filters.get('only_grades'):
        # filter for courses that have requirements and grades arent empty
        courses = courses.filter(
            entryrequirement__has_requirements=True,
            entryrequirement__display_grades__isnull=False
        ).exclude(
            entryrequirement__display_grades=''
        ).distinct()
    # endif

    # if user wants to see only courses with no requirements
    if filters.get('no_requirements'):
        # filter for courses where has_requirements is false
        courses = courses.filter(
            entryrequirement__has_requirements=False
        ).distinct()
    # endif
    # If the query is a location, show one course per university
    # Otherwise, show all matching courses
    query_for_match = query.strip()
    show_all_courses = True
    is_location_query = False

    if query_for_match:
        if University.objects.filter(location__icontains=query_for_match).exists():
            is_location_query = True
        # endif

        region_map = filters.get('region_mapping', {})
        for cities in region_map.values():
            for city in cities:
                if query_for_match.lower() == city.lower():
                    is_location_query = True
                    break
                # endif
            # endfor
            if is_location_query:
                break
            # endif
        # endfor
    # endif

    if is_location_query:
        show_all_courses = False
    # endif

    if query_for_match:
        exact_unis = University.objects.filter(name__iexact=query_for_match)
        if exact_unis.exists():
            courses = courses.filter(university__in=exact_unis)
            show_all_courses = True
        else:
            matching_unis = University.objects.filter(name__icontains=query_for_match)
            if matching_unis.count() == 1:
                courses = courses.filter(university__in=matching_unis)
                show_all_courses = True
            # endif
        # endif
    # endif

    courses = courses.order_by("university__name", "name")

    # pick one representative course per university to keep layout consistent
    if show_all_courses:
        selected_courses = courses
    else:
        selected_courses = []
        seen_universities = set()
        for course in courses:
            uni_id = course.university_id
            if uni_id in seen_universities:
                continue
            # endif
            seen_universities.add(uni_id)
            selected_courses.append(course)
            if len(selected_courses) >= 200:
                break
            # endif
        # endfor
    # endif

    # format everything for display (one row per university)
    for course in selected_courses:
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

        link = course.link
        if not link:
            link = "#"
        # endif

        match = UniMatchResult(
            university=course.university.name,
            course=course.name,
            course_type=course.course_type,
            duration=course.duration,
            requirements=requirements_str,
            course_link=link
        )
        results.append(match)
    # endfor

    return results
# enddef
