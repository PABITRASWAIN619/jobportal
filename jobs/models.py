from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser

# =========================
# 👤 PROFILE
# =========================
# =========================
# 👤 PROFILE (UPDATED)
# =========================
class Profile(models.Model):
    ROLE_CHOICES = (
        ('jobseeker', 'Job Seeker'),
        ('recruiter', 'Recruiter'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='jobseeker')

    profile_pic = models.ImageField(upload_to='profile/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)

    skills = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)

    # ================= NEW FEATURES =================
    phone = models.CharField(max_length=15, blank=True)

    notifications_enabled = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)

    two_factor_enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    # ================= PROFILE COMPLETION =================
    def profile_completion(self):
        score = 0

        if self.user.username:
            score += 15
        if self.user.email:
            score += 15
        if self.profile_pic:
            score += 20
        if self.resume:
            score += 20
        if self.skills:
            score += 15
        if self.location:
            score += 10
        if self.phone:
            score += 5

        return score

# =========================
# 💼 JOB
# =========================
class Job(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# =========================
# 📄 APPLICATION
# =========================
class Application(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('viewed', 'Viewed'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')

    recruiter_feedback = models.TextField(blank=True, null=True)

    resume = models.FileField(upload_to='resumes/', blank=True, null=True)

    linkedin = models.URLField(blank=True, null=True)  # ✅ ADD THIS

    viewed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    applied_at = models.DateTimeField(auto_now_add=True)

# =========================
# 🧠 POST
# =========================
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


# =========================
# 🔔 NOTIFICATION
# =========================
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


# =========================
# 💬 MESSAGE
# =========================
class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


# =========================
# 🆘 SUPPORT
# =========================
class SupportMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
  
