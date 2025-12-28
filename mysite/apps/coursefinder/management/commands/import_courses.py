"""
Import uni course data from the WebScraper JSON files
"""

import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from mysite.apps.coursefinder.models import University, Course, EntryRequirement, SubjectRequirement


class Command(BaseCommand):
    help = 'Import unis and courses from WebScraper JSON'

    def add_arguments(self, parser):
        # path to json file
        parser.add_argument(
            'json_file',
            type=str,
            help='JSON file path from WebScraper'
        )

        # verbose flag for more output
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show more details'
        )

    # enddef

    @transaction.atomic  # makes sure everything saves or nothing saves
    def handle(self, *args, **options) -> None:
        json_file_path: str = options['json_file']
        verbose: bool = options.get('verbose', False)

        # starting message
        print(f"Starting import from {json_file_path}...")

        # open the json file
        try:
            with open(json_file_path, 'r') as file:
                universities_data: list = json.load(file)
        except FileNotFoundError:
            raise CommandError(f"Could not find file: {json_file_path}")
        except json.JSONDecodeError:
            raise CommandError(f"Invalid JSON in file: {json_file_path}")
        # endtry

        # make sure its a list of unis
        if not isinstance(universities_data, list):
            raise CommandError("JSON should be a list of unis")
        # endif

        # counters for summary
        total_universities: int = 0
        total_courses: int = 0
        total_requirements: int = 0

        # go through each uni
        for uni_data in universities_data:
            total_universities = total_universities + 1

            # add or update uni in database
            university, uni_created = University.objects.update_or_create(
                name=uni_data['name'],
                defaults={
                    'location': uni_data.get('location', ''),
                    'website': uni_data.get('link', ''),
                    'all_courses_url': uni_data.get('link_all_courses', ''),
                }
            )

            if verbose:
                if uni_created:
                    print(f"Added uni: {university.name}")
                else:
                    print(f"Updated uni: {university.name}")
            # endif

            # get all courses for this uni
            courses = uni_data.get('courses', [])

            for course_data in courses:
                total_courses = total_courses + 1

                # add or update course
                course, course_created = Course.objects.update_or_create(
                    university=university,
                    name=course_data['name'],
                    defaults={
                        'course_type': course_data.get('course_type', ''),
                        'duration': course_data.get('duration', ''),
                        'mode': course_data.get('mode', ''),
                        'location': course_data.get('location', ''),
                        'start_date': course_data.get('start_date', ''),
                        'link': course_data.get('link', ''),
                    }
                )

                if verbose and course_created:
                    print(f"  - Added course: {course.name}")
                # endif

                # get requirements
                requirements = course_data.get('requirements', [])

                # just use first requirement (some courses have multiple)
                if requirements and len(requirements) > 0:
                    req_data = requirements[0]

                    # add or update requirements
                    entry_req, req_created = EntryRequirement.objects.update_or_create(
                        course=course,
                        defaults={
                            'min_ucas_points': req_data.get('min_ucas_points', 0),
                            'min_grade_required': req_data.get('min_grade_required', ''),
                            'display_grades': req_data.get('display_grades', ''),
                            'btec_grades': req_data.get('btec_grades', ''),
                            'accepts_ucas': req_data.get('accepts_ucas', True),
                            'has_requirements': req_data.get('has_requirements', True),
                        }
                    )

                    total_requirements = total_requirements + 1

                    # delete old subject requirements and add fresh ones
                    entry_req.subject_requirements.all().delete()

                    # add subject specific requirements
                    subject_reqs = req_data.get('subject_requirements', [])
                    for sub_req_data in subject_reqs:
                        SubjectRequirement.objects.create(
                            entry_requirement=entry_req,
                            subject=sub_req_data['subject'],
                            grade=sub_req_data['grade'],
                        )

                        if verbose:
                            print(f"    - Subject req: {sub_req_data['subject']} needs {sub_req_data['grade']}")
                        # endif
                    # endfor
                # endif
            # endfor (courses)
        # endfor (universities)

        # show results
        print("\nDone!")
        print(f"Unis: {total_universities}")
        print(f"Courses: {total_courses}")
        print(f"Requirements: {total_requirements}")
    # enddef
# endclass
