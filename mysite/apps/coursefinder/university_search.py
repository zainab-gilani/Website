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
    #endif
    
    query_lower = query.strip().lower()
    
    # Get course synonyms
    courses = SYNONYMS.get('courses', {})
    
    # Check if query is a synonym for any subject
    for subject, synonym_list in courses.items():
        for synonym in synonym_list:
            if synonym.lower() == query_lower:
                # Found a match - return just the main subject name
                return [subject.lower()]
            #endif
        #endfor
    #endfor
    
    # If no synonym found, return original query
    return [query_lower]
#enddef


def search_universities(query: str, filters: dict = None) -> List:
    """
    Searches for universities and courses based on general text query.

    :param query: Search string (university name, location, or course name)
    :param filters: Optional dictionary containing filter options (course_type, duration, mode, location)
    :return: List of UniMatchResult objects containing matching courses
    """

    if not query:
        return []
    #endif

    if filters is None:
        filters = {}
    #endif

    # Get all search terms including synonyms
    search_terms = expand_query_with_synonyms(query)

    results = []

    # Build search query using all terms
    course_query = Q()
    for term in search_terms:
        # Search in course name, university name, and location
        term_query = Q(name__icontains=term) | Q(university__name__icontains=term) | Q(university__location__icontains=term)
        course_query |= term_query
    #endfor

    courses = Course.objects.select_related('university').prefetch_related('entryrequirement').filter(course_query)

    # add filters
    if filters.get('course_type'):
        courses = courses.filter(course_type=filters['course_type'])
    #endif
    if filters.get('duration'):
        courses = courses.filter(duration=filters['duration'])
    #endif
    if filters.get('mode'):
        courses = courses.filter(mode=filters['mode'])
    #endif
    if filters.get('location'):
        courses = courses.filter(location=filters['location'])
    #endif

    if filters.get('ucas_range'):
        # Filter by minimum UCAS points
        try:
            min_points = int(filters['ucas_range'])
            courses = courses.filter(entryrequirement__min_ucas_points__lte=min_points)
        except ValueError:
            pass
        #endtry
    #endif

    # if user wants to see only courses with grade requirements
    if filters.get('only_grades'):
        # filter for courses that have requirements and grades arent empty
        courses = courses.filter(
            entryrequirement__has_requirements=True,
            entryrequirement__display_grades__isnull=False
        ).exclude(
            entryrequirement__display_grades=''
        ).distinct()
    #endif

    # if user wants to see only courses with no requirements
    if filters.get('no_requirements'):
        # filter for courses where has_requirements is false
        courses = courses.filter(
            entryrequirement__has_requirements=False
        ).distinct()
    #endif

    courses = courses[:30]

    # format everything for display
    for course in courses:
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
                #endif

                # add btec grades if they exist
                if req.btec_grades:
                    requirements_str += f" / {req.btec_grades}"
                #endif
            else:
                # no requirements for this course
                requirements_str = "No specific requirements"
            #endif
        except:
            requirements_str = "No specific requirements"
        #endtry

        match = UniMatchResult(
            university=course.university.name,
            course=course.name,
            course_type=course.course_type,
            duration=course.duration,
            requirements=requirements_str,
            course_link=course.link or "#"
        )
        results.append(match)
    #endfor

    return results
#enddef