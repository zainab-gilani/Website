"""
University search service for general text-based searching
"""
from typing import List
from django.db.models import Q
from .models import University, Course
from .types import UniMatchResult
from ..nlp.synonyms import SYNONYMS


def expand_query_with_synonyms(query: str) -> List[str]:
    """Convert query to main subject name if it's a synonym"""
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
    Search for universities and courses based on general text query.
    This searches university names, locations, and course names.

    Examples:
    - "Manchester" - finds unis in Manchester or with Manchester in the name
    - "University of Oxford" - finds Oxford uni
    - "Computer Science" - finds CS courses at any uni
    - "London" - finds all London-based universities
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

    courses = courses[:30]

    # format everything for display
    for course in courses:
        try:
            req = course.entryrequirement
            requirements_str = req.display_grades or f"{req.min_ucas_points} UCAS points"
            if req.btec_grades:
                requirements_str += f" / {req.btec_grades}"
            #endif
        except:
            requirements_str = "Requirements not specified"
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