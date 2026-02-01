from django.db import models
from django.contrib.auth.models import User


class SavedMatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_matches")
    university = models.CharField(max_length=200)
    course = models.CharField(max_length=200)
    course_type = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    requirements = models.CharField(max_length=300)
    course_link = models.URLField(max_length=500)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "university", "course", "course_link"],
                name="unique_saved_match_per_user"
            )
        ]
    #endclass

    def __str__(self):
        return f"{self.user.username} - {self.university} ({self.course})"
    # enddef
# endclass
