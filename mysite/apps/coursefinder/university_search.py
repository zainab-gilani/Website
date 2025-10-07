"""
University search service for general text-based searching
"""
from typing import List
from django.db.models import Q
from .models import University, Course
from .types import UniMatchResult
from ..nlp.synonyms import SYNONYMS


def expand_query_with_synonyms(query: str) -> List[str]:
    """Add synonyms to search query for better matching"""
    if not query:
        return []
    #endif
    
    query_lower = query.strip().lower()
    search_terms = [query_lower]  # Always include original query
    
    # Check each subject in synonyms to see if query matches
    for subject, synonym_list in SYNONYMS.items():
        # If query matches any synonym, add all synonyms for that subject
        for synonym in synonym_list:
            if synonym.lower() == query_lower:
                # Add all other synonyms for this subject
                for other_synonym in synonym_list:
                    if other_synonym.lower() not in search_terms:
                        search_terms.append(other_synonym.lower())
                    #endif
                #endfor
                break  # Found a match, no need to check other synonyms
            #endif
        #endfor
    #endfor
    
    return search_terms
#enddef


def search_universities(query: str) -> List:
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
    
    courses = Course.objects.select_related('university').prefetch_related('entryrequirement').filter(course_query)[:30]

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