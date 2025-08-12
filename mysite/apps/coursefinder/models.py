from django.db import models

# Create your models here.

class University(models.Model):
    name = models.CharField(max_length=200, unique=True)
    location = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True) # Link to uni
    all_courses_url = models.URLField(blank=True) # "View all courses" page

    def __str__(self):
        return self.name
    #enddef
#endclass

class Course(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    course_type = models.CharField(max_length=50, blank=True) # e.g. BSc (Hons)
    duration = models.CharField(max_length=50, blank=True)
    mode = models.CharField(max_length=30, blank=True) # Full time / Part time
    location = models.CharField(max_length=200, blank=True)
    start_date = models.CharField(max_length=50, blank=True)
    link = models.URLField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.university.name}"
    #enddef
#endclass

class EntryRequirement(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE)

    min_ucas_points = models.IntegerField(default=0)
    display_grade = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"requirements for {self.course.name}"
    #enddef
#endclass