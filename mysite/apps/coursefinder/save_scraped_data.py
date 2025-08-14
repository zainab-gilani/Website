from .models import University, Course, EntryRequirement

def saved_Data(scraped_unis):
    for uni_data in scraped_unis:
        uni = University.objects.create(
            name=uni_data.name,
            location=uni_data.location,
            link=uni_data.link,
            link_all_courses=uni_data.link_all_courses
        )

        for course_data in uni_data.courses:
            course = Course.objects.create(
                university=uni,
                name=course_data.name,
                course_type=course_data.course_type,
                duration=course_data.duration,
                mode=course_data.mode,
                location=course_data.location,
                start_date=course_data.start_data,
                link=course_data.link
            )

            for req_data in course_data.requirements:
                EntryRequirement.objects.create(
                    course=course,
                    min_ucas_points=req_data.min_ucas_points,

                )