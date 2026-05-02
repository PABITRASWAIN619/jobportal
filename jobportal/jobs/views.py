from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone

import random

from .models import Job, Application, Profile, SupportMessage


# ===========================
# 🔐 AUTH - LOGIN
# ===========================
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user_obj = User.objects.filter(email=email).first()

        if not user_obj:
            messages.error(request, "Invalid credentials")
            return render(request, "login.html", {"hide_navbar": True})

        user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)

            if user.is_superuser:
                return redirect("/admin-dashboard/")

            return redirect("/home/")

        messages.error(request, "Invalid credentials")
        return render(request, "login.html", {"hide_navbar": True})

    return render(request, "login.html", {"hide_navbar": True})


# ===========================
# 🆕 SIGNUP
# ===========================
def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("/signup/")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name
        )

        Profile.objects.create(user=user, role=role)

        messages.success(request, "Account created successfully")
        return redirect("/login/")

    return render(request, "signup.html", {"hide_navbar": True})


# ===========================
# 🔢 OTP VERIFY
# ===========================
def verify_otp(request):
    if request.method == "POST":
        user_otp = request.POST.get('otp')
        real_otp = request.session.get('otp')
        email = request.session.get('email')

        if not real_otp or not email:
            messages.error(request, "Session expired")
            return redirect('/login/')

        if str(user_otp) == str(real_otp):

            user, created = User.objects.get_or_create(
                email=email,
                defaults={"username": email.split("@")[0]}
            )

            if created:
                user.set_unusable_password()
                user.save()

            login(request, user)

            return redirect("/home/")

        else:
            messages.error(request, "Invalid OTP")

    return render(request, "verify_otp.html", {"hide_navbar": True})


# ===========================
# 📩 SEND OTP
# ===========================
def send_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if not email:
            messages.error(request, "Email is required")
            return render(request, "send_otp.html", {"hide_navbar": True})

        otp = random.randint(100000, 999999)

        request.session["otp"] = str(otp)
        request.session["email"] = email
        request.session["otp_time"] = str(timezone.now())

        send_mail(
            subject="Your OTP for Login",
            message=f"Your OTP is: {otp}",
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(request, "OTP sent successfully!")
        return redirect("/verify-otp/")

    return render(request, "send_otp.html", {"hide_navbar": True})


# ===========================
# 🏢 APPLY JOB
# ===========================
@login_required
def apply_job(request, job_id):
    if request.user.profile.role != 'jobseeker':
        return redirect('/')

    job = get_object_or_404(Job, id=job_id)

    if Application.objects.filter(user=request.user, job=job).exists():
        messages.warning(request, "Already applied")
        return redirect('/jobs/')

    if request.method == "POST":
        Application.objects.create(
            user=request.user,
            job=job,
            resume=request.FILES.get('resume'),
            linkedin=request.POST.get('linkedin')
        )

        messages.success(request, "Application submitted")
        return redirect('/jobs/')

    return render(request, 'apply.html', {'job': job})


# ===========================
# 🏢 RECRUITER
# ===========================
@login_required
def post_job(request):
    if request.user.profile.role != 'recruiter':
        return redirect('/')

    if request.method == "POST":
        Job.objects.create(
            title=request.POST.get('title'),
            company=request.POST.get('company'),
            location=request.POST.get('location'),
            description=request.POST.get('description'),
            posted_by=request.user
        )

        messages.success(request, "Job posted")
        return redirect('/jobs/')

    return render(request, 'post_job.html')


@login_required
def recruiter_dashboard(request):
    jobs = Job.objects.filter(posted_by=request.user)
    applications = Application.objects.filter(job__in=jobs)

    return render(request, 'recruiter_dashboard.html', {
        'jobs': jobs,
        'applications': applications
    })


# ===========================
# 📌 UPDATE STATUS
# ===========================
@login_required
def update_status(request, app_id, status):
    app = get_object_or_404(Application, id=app_id)

    if request.user != app.job.posted_by:
        return redirect('/')

    app.status = status
    app.save()

    send_mail(
        'Application Update',
        f'Your application is {status}',
        'admin@jobportal.com',
        [app.user.email],
        fail_silently=True,
    )

    return redirect('/recruiter-dashboard/')


# ===========================
# 👤 USER FEATURES
# ===========================
@login_required
def my_applications(request):
    applications = Application.objects.filter(user=request.user).select_related('job')

    return render(request, 'my_applications.html', {
        'applications': applications
    })

@login_required
def profile(request):
    profile = request.user.profile

    if request.method == "POST":
        request.user.first_name = request.POST.get("name")
        request.user.email = request.POST.get("email")
        request.user.save()

        if request.FILES.get("profile_pic"):
            profile.profile_pic = request.FILES["profile_pic"]

        profile.save()

        messages.success(request, "Profile updated successfully")
        return redirect("/profile/")

    return render(request, "profile.html", {"profile": profile})


@login_required
def settings(request):
    if request.method == "POST":
        password = request.POST.get('password')

        if password:
            request.user.set_password(password)
            request.user.save()
            messages.success(request, "Password updated")
            return redirect('/login/')

    return render(request, 'settings.html')


def support(request):
    if request.method == "POST":
        message = request.POST.get('message')

        send_mail(
            'Support Request',
            message,
            request.user.email if request.user.is_authenticated else 'anonymous',
            ['admin@jobportal.com'],
            fail_silently=True,
        )

        messages.success(request, "Support request sent")

    return render(request, 'support.html')


# ===========================
# 💬 CHAT
# ===========================
@login_required
def chat(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'chat.html', {'users': users})


@login_required
def send_message(request):
    if request.method == "POST":
        receiver_id = request.POST.get('receiver')
        text = request.POST.get('text')

    return redirect('/chat/')


# ===========================
# 📊 DASHBOARD
# ===========================
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


@login_required
def create_post(request):
    if request.method == "POST":
        return redirect('/dashboard/')

    return render(request, 'create_post.html')


# ===========================
# 🚪 LOGOUT
# ===========================
def logout_view(request):
    logout(request)
    return redirect('/login/')


# ===========================
# 🏠 HOME
# ===========================
def home(request):
    return render(request, "home.html")


# ===========================
# 📄 JOB LIST
# ===========================
def job_list(request):
    return render(request, "job_list.html")


# ===========================
# ===========================
# 🛠 ADMIN PAGES (FIXED)
# ===========================
@staff_member_required(login_url='/login/')
def admin_dashboard(request):
    return render(request, "admin_dashboard.html")


@staff_member_required(login_url='/login/')
def admin_post_job(request):
    if request.method == "POST":
        Job.objects.create(
            title=request.POST.get("title"),
            company=request.POST.get("company"),
            location=request.POST.get("location"),
            description=request.POST.get("description"),
            posted_by=request.user
        )
        return redirect('/admin-dashboard/')

    return render(request, "admin_post_job.html")


@staff_member_required(login_url='/login/')
def admin_users(request):
    return render(request, "admin_users.html")


@staff_member_required(login_url='/login/')
def admin_jobs(request):
    return render(request, "admin_jobs.html")


@staff_member_required(login_url='/login/')
def admin_applications(request):
    return render(request, "admin_applications.html")
@login_required
def update_status(request, app_id, status):
    app = Application.objects.get(id=app_id)

    app.status = status

    if status == "viewed":
        app.viewed_at = timezone.now()

    app.save()
    return redirect('recruiter_dashboard')