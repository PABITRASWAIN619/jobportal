from django.db import models

class User(models.Model):
    ROLE_CHOICES = (
        ('jobseeker', 'Job Seeker'),
        ('recruiter', 'Recruiter'),
    )

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return self.name


class Job(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Application(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/')
    linkedin = models.URLField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.name} - {self.job.title}"