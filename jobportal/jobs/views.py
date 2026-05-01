from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone

from datetime import timedelta
import random

from .models import Job, Application, Profile
# (Optional if you created these)
# from .models import Post, Notification, Message


# ===========================
# 🔐 AUTH
# ===========================
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

def login_view(request):
    
    # 🚨 IMPORTANT: only redirect if already logged in
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin-dashboard/')
        return redirect('/home/')

    # ONLY POST should authenticate
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = None

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            pass

        if user is not None:
            login(request, user)

            if user.is_superuser:
                return redirect('/admin-dashboard/')
            return redirect('/home/')

        messages.error(request, "Invalid email or password ❌")

    return render(request, 'login.html')
# ===========================
# 🔢 OTP LOGIN
# ===========================

import random
from django.contrib.auth.models import User
from django.core.mail import send_mail

def send_otp(request):
    if request.method == "POST":
        email = request.POST.get('email')

        # ✅ generate OTP
        otp = str(random.randint(100000, 999999))

        # ✅ jobs in session
        request.session['otp'] = otp
        request.session['email'] = email

        # ✅ send email
        send_mail(
            'Your OTP Code',
            f'Your OTP is {otp}',
            'yourgmail@gmail.com',
            [email],
            fail_silently=False,
        )

        return redirect('/verify-otp/')

    return render(request, 'send_otp.html')

from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User

def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        # ❌ check duplicate user
        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already exists")
            return redirect("/signup/")

        # ✅ create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name
        )

        # ⚠️ If you DON'T have Profile model, remove this block
        try:
            user.profile.role = role
            user.profile.save()
        except:
            pass

        messages.success(request, "Account created successfully!")
        return redirect("/login/")

    return render(request, "signup.html")

def verify_otp(request):
    if request.method == "POST":
        user_otp = request.POST.get('otp')
        real_otp = request.session.get('otp')
        email = request.session.get('email')

        if user_otp == real_otp:

            user, created = User.objects.get_or_create(
                username=email,
                defaults={'email': email}
            )

            # ✅ SAFE profile creation
            Profile.objects.get_or_create(
                user=user,
                defaults={'role': 'jobseeker'}
            )

            login(request, user)

            return redirect('/home/')

        else:
            messages.error(request, "Invalid OTP")

    return render(request, 'verify_otp.html')
# ===========================
# 🏠 HOME
# ===========================

@login_required(login_url='/login/')
def home(request):
    jobs = Job.objects.all()[:6]
    companies = Job.objects.values_list('company', flat=True).distinct()

    return render(request, 'home.html', {
        'jobs': jobs,
        'companies': companies
    })


# ===========================
# 💼 JOBS
# ===========================

@login_required
def job_list(request):
    query = request.GET.get('q')
    location = request.GET.get('location')

    jobs = Job.objects.all()

    if query:
        jobs = jobs.filter(title__icontains=query)

    if location:
        jobs = jobs.filter(location__icontains=location)

    return render(request, 'jobs.html', {'jobs': jobs})


@login_required
def apply_job(request, job_id):
    if request.user.profile.role != 'jobseeker':
        return redirect('/')

    job = get_object_or_404(Job, id=job_id)

    if Application.objects.filter(user=request.user, job=job).exists():
        messages.warning(request, "Already applied")
        return redirect('/jobs/')

    if request.method == "POST":
        resume = request.FILES.get('resume')
        linkedin = request.POST.get('linkedin')

        Application.objects.create(
            user=request.user,
            job=job,
            resume=resume,
            linkedin=linkedin
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
    if request.user.profile.role != 'recruiter':
        return redirect('/')

    jobs = Job.objects.filter(posted_by=request.user)
    applications = Application.objects.filter(job__in=jobs)

    return render(request, 'recruiter_dashboard.html', {
        'applications': applications
    })


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
    apps = Application.objects.filter(user=request.user)
    return render(request, 'my_applications.html', {'applications': apps})


from django.shortcuts import render, redirect
@login_required
def profile(request):
    profile = request.user.profile

    if request.method == "POST":
        # ✅ update name + email
        request.user.first_name = request.POST.get("name")
        request.user.email = request.POST.get("email")
        request.user.save()

        # ✅ profile image fix
        if request.FILES.get("profile_pic"):
            profile.profile_pic = request.FILES["profile_pic"]

        profile.save()

        messages.success(request, "Profile updated successfully ✅")
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

            return redirect('/login/')  # IMPORTANT

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
# 👑 ADMIN
# ===========================
@staff_member_required(login_url='/login/')
def admin_dashboard(request):
    users = User.objects.all()
    jobs = Job.objects.all()
    applications = Application.objects.all()
    support_msgs = SupportMessage.objects.all()

    return render(request, 'admin_dashboard.html', {
        'users': users,
        'jobs': jobs,
        'applications': applications,
        'support_msgs': support_msgs,
    })


# ===========================
# 💬 CHAT (BASIC)
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

        # Example if Message model exists:
        # Message.objects.create(
        #     sender=request.user,
        #     receiver_id=receiver_id,
        #     text=text
        # )

    return redirect('/chat/')
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')
@login_required
def create_post(request):
    if request.method == "POST":
        content = request.POST.get('content')

        # ⚠️ Only if Post model exists
        # Post.objects.create(user=request.user, content=content)

        return redirect('/dashboard/')

    return render(request, 'create_post.html')
from django.shortcuts import redirect
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('/login/')
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from .models import Job, Application, Profile

from django.contrib.admin.views.decorators import staff_member_required
from .models import SupportMessage

@staff_member_required(login_url='/login/')
def admin_dashboard(request):
    users = User.objects.all()
    jobs = Job.objects.all()
    applications = Application.objects.all()
    support_msgs = SupportMessage.objects.all()

    return render(request, 'admin_dashboard.html', {
        'users': users,
        'jobs': jobs,
        'applications': applications,
        'support_msgs': support_msgs
    })
    
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required(login_url='/login/')
def admin_post_job(request):
    if request.method == "POST":
        Job.objects.create(
            title=request.POST.get("title"),
            company=request.POST.get("company"),
            location=request.POST.get("location"),
            description=request.POST.get("description"),
            status='active',
            posted_by=request.user
        )
        return redirect('/admin-dashboard/')
@login_required
@staff_member_required
def admin_reply(request, id):
    msg = SupportMessage.objects.get(id=id)

    if request.method == "POST":
        msg.reply = request.POST.get("reply")
        msg.save()

    return redirect('/admin-dashboard/')