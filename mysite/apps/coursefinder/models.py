from django.db import models

# Create your models here.

class University(models.Model):
    name = models.CharField(max_length=200, unique=True)
    location = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)  # Link to uni
    all_courses_url = models.URLField(blank=True)  # "View all courses" page

    def __str__(self):
        return self.name
    # enddef
# endclass

class Course(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    course_type = models.CharField(max_length=50, blank=True)  # e.g. BSc (Hons)
    duration = models.CharField(max_length=50, blank=True)
    mode = models.CharField(max_length=30, blank=True)  # Full time / Part time
    location = models.CharField(max_length=200, blank=True)
    start_date = models.CharField(max_length=50, blank=True)
    link = models.URLField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.university.name}"
    # enddef
# endclass

class EntryRequirement(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE)
    
    # Core fields for filtering and validation
    min_ucas_points = models.IntegerField(default=0, db_index=True)  # Indexed for fast queries
    min_grade_required = models.CharField(max_length=2, blank=True)  # 'B' for BBB, 'C' for BCC
    
    # Display fields
    display_grades = models.CharField(max_length=50, blank=True)  # "AAB" or "BCC-BBB"
    btec_grades = models.CharField(max_length=20, blank=True)  # "DMM", "D*D*D*"
    
    # Flags
    accepts_ucas = models.BooleanField(default=True)  # Some unis don't accept UCAS points
    has_requirements = models.BooleanField(default=True)  # False if no requirements

    def __str__(self):
        return f"Requirements for {self.course.name}"
    # enddef
# endclass

class SubjectRequirement(models.Model):
    """
    Specific subject requirements for a course.
    """
    entry_requirement = models.ForeignKey(
        EntryRequirement, 
        on_delete=models.CASCADE,
        related_name='subject_requirements'  # Access from EntryRequirement
    )
    subject = models.CharField(max_length=100)  # e.g. "Mathematics"
    grade = models.CharField(max_length=2)  # e.g. "A"
    
    class Meta:
        # Ensure no duplicate subject requirements for same course
        unique_together = ['entry_requirement', 'subject']
    
    def __str__(self):
        return f"{self.subject}: {self.grade}"
    # enddef
# endclass