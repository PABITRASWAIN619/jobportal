
from django.conf import settings
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
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Profile

User = get_user_model()

def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        # ✅ Check if user already exists
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": name}
        )

        if created:
            user.set_password(password)
            user.save()

        # ✅ FIX: avoid duplicate profile
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={"role": role}
        )

        messages.success(request, "Signup successful!")
        return redirect("/login/")

    return render(request, "signup.html")


# ===========================
# 🔢 OTP VERIFY
# ===========================
from django.contrib.auth import login, get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages

User = get_user_model()

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

            # ✅ IMPORTANT FIX
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            return redirect("/home/")

        else:
            messages.error(request, "Invalid OTP")

    return render(request, "verify_otp.html", {"hide_navbar": True})
# ===========================
# 📩 SEND OTP
# ===========================
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import random

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

        try:
            send_mail(
                subject="Your OTP for Login",
                message=f"Your OTP is: {otp}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
             print("EMAIL ERROR:", e)
             messages.error(request, "OTP sending failed. Check server logs.")
             return render(request, "send_otp.html", {"hide_navbar": True})

        messages.success(request, "OTP sent successfully!")
        return redirect("/verify-otp/")

    return render(request, "send_otp.html", {"hide_navbar": True})


# ===========================
# 🏢 APPLY JOB
# ===========================
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == "POST":

        email = request.POST.get("email")
        phone = request.POST.get("phone")
        linkedin = request.POST.get("linkedin")
        resume = request.FILES.get("resume")

        # ✅ LinkedIn validation
        if linkedin and "linkedin.com" not in linkedin:
            messages.error(request, "Please enter a valid LinkedIn URL")
            return redirect(request.path)

        # ✅ Save everything
        Application.objects.create(
            user=request.user,
            job=job,
            email=email,
            phone=phone,
            linkedin=linkedin,
            resume=resume
        )

        messages.success(request, "Application submitted successfully!")
        return redirect("job_list")

    return render(request, "apply.html", {"job": job})
def job_list(request):
    
    jobs = Job.objects.filter(status='active')

    # 🔥 EASY APPLY FILTER LOGIC
    if request.GET.get("filter") == "easy":
        jobs = jobs.filter(status='active')  # you can improve later

    jobs = jobs.order_by('-created_at')

    context = {
        "jobs": jobs
    }

    return render(request, "jobs.html", context)
# ===========================
# 🏢 RECRUITER
# ===========================
@login_required
def post_job(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if profile.role != 'recruiter':
        return redirect('/')

    if request.method == "POST":
        Job.objects.create(
            title=request.POST.get('title'),
            company=request.POST.get('company'),
            location=request.POST.get('location'),
            description=request.POST.get('description'),
            posted_by=request.user
        )

        messages.success(request, "Job posted successfully")
        return redirect('/dashboard/jobs/')

    return render(request, "admin_post_job.html")


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
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Profile


@login_required
def profile(request):
    # ✅ SAFE: auto-create profile if missing
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        request.user.first_name = request.POST.get("name")
        request.user.email = request.POST.get("email")
        request.user.save()

        if request.FILES.get("profile_pic"):
            profile.profile_pic = request.FILES["profile_pic"]

        profile.save()

        messages.success(request, "Profile updated successfully")
        return redirect("profile")

    return render(request, "profile.html", {"profile": profile})

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Profile


@login_required
def user_settings(request):
    user = request.user

    # ✅ SAFE: prevents "User has no profile" crash
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == "POST":

        # ================= BASIC INFO =================
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")
        user.save()

        profile.phone = request.POST.get("phone")
        profile.skills = request.POST.get("skills")
        profile.location = request.POST.get("location")

        # ================= FILE UPLOAD =================
        if request.FILES.get("profile_pic"):
            profile.profile_pic = request.FILES["profile_pic"]

        if request.FILES.get("resume"):
            profile.resume = request.FILES["resume"]

        # ================= TOGGLES =================
        profile.notifications_enabled = request.POST.get("notifications") == "on"
        profile.dark_mode = request.POST.get("dark_mode") == "on"
        profile.two_factor_enabled = request.POST.get("two_factor") == "on"

        profile.save()

        messages.success(request, "Settings updated successfully!")
        return redirect("user_settings")

    return render(request, "settings.html", {
        "profile": profile
    })
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import SupportMessage

@login_required
def support(request):
    if request.method == "POST":
        msg_text = request.POST.get('message')

        # ✅ PUT IT HERE (THIS IS THE CORRECT PLACE)
        SupportMessage.objects.create(
            user=request.user,
            email=request.user.email,
            message=msg_text
        )

        messages.success(request, "Support request sent successfully!")
        return redirect("support")

    support_msgs = SupportMessage.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'support.html', {
        "support_msgs": support_msgs
    })

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
        receiver_id = request.POST.get("receiver")
        message = request.POST.get("message")

        ChatMessage.objects.create(
            sender=request.user,
            receiver_id=receiver_id,
            message=message
        )

    return redirect("/chat/")
@login_required
def chat(request):
    users = User.objects.exclude(id=request.user.id)

    messages = ChatMessage.objects.filter(
        receiver=request.user
    ) | ChatMessage.objects.filter(
        sender=request.user
    )

    messages = messages.order_by("created_at")

    return render(request, "chat.html", {
        "users": users,
        "messages": messages
    })

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
from django.shortcuts import render
from django.contrib.auth.models import User
from .models import Job, Application, SupportMessage

from django.contrib.auth import get_user_model
User = get_user_model()

from django.contrib.auth.models import User
from .models import Job, Application, SupportMessage

def admin_dashboard(request):
    users = User.objects.all().order_by('-id')
    jobs = Job.objects.all().order_by('-id')
    applications = Application.objects.all()

    support_msgs = SupportMessage.objects.select_related("user").order_by("-id")

    stats = {
        "total_users": users.count(),
        "total_jobs": jobs.count(),
        "total_apps": applications.count(),
    }

    analytics = {
        "pending": applications.filter(status="applied").count(),
        "accepted": applications.filter(status="accepted").count(),
        "rejected": applications.filter(status="rejected").count(),
    }

    print("USERS:", users.count())
    print("JOBS:", jobs.count())

    return render(request, "admin_dashboard.html", {
        "users": users,
        "jobs": jobs,
        "applications": applications,
        "support_msgs": support_msgs,
        "stats": stats,
        "analytics": analytics,
    })
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


from django.contrib.auth.models import User

def admin_users(request):
    users = User.objects.all()
    return render(request, "admin_users.html", {"users": users})


from django.core.paginator import Paginator

def admin_jobs(request):
    job_list = Job.objects.all().order_by('-id')

    paginator = Paginator(job_list, 5)
    page_number = request.GET.get('page')
    jobs = paginator.get_page(page_number)

    return render(request, "jobs/admin_jobs.html", {"jobs": jobs})

def admin_applications(request):
    applications = Application.objects.select_related('user', 'job').all()
    return render(request, "jobs/admin_applications.html", {"applications": applications})
    
@login_required
def update_status(request, app_id, status):
    app = Application.objects.get(id=app_id)

    app.status = status

    if status == "viewed":
        app.viewed_at = timezone.now()

    app.save()
    return redirect('recruiter_dashboard')
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from .models import Application


@csrf_exempt  # remove this if you properly send CSRF token via AJAX
def update_application_status(request):
    if request.method == "POST":
        app_id = request.POST.get("id")
        status = request.POST.get("status")

        # ✅ Validate input
        if not app_id or not status:
            return JsonResponse({
                "success": False,
                "error": "Missing data"
            })

        try:
            app = Application.objects.get(id=app_id)

            # ✅ Update status
            app.status = status

            # ✅ Mark viewed time
            if status == "viewed" and not app.viewed_at:
                app.viewed_at = now()

            app.save()

            return JsonResponse({
                "success": True,
                "new_status": app.get_status_display()
            })

        except Application.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Application not found"
            })

    # ❌ Wrong method
    return JsonResponse({
        "success": False,
        "error": "Invalid request method"
    })
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Job

@login_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == "POST":
        job.title = request.POST.get('title')
        job.company = request.POST.get('company')
        job.location = request.POST.get('location')
        job.description = request.POST.get('description')
        job.save()

        messages.success(request, "Job updated successfully ✅")
        return redirect('/dashboard/jobs/')

    return render(request, 'jobs/edit_job.html', {'job': job})
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Job

def delete_job(request, job_id):
    print("DELETE REQUEST HIT")   # 👈 DEBUG HERE

    if request.method == "POST":
        print("Job ID:", job_id)

        job = get_object_or_404(Job, id=job_id)
        job.delete()

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request method"})
def admin_dashboard(request):
    total_jobs = Job.objects.count()
    total_users = User.objects.count()
    total_apps = Application.objects.count()
    accepted = Application.objects.filter(status="accepted").count()

    return render(request, "admin_dashboard.html", {
        "total_jobs": total_jobs,
        "total_users": total_users,
        "total_apps": total_apps,
        "accepted": accepted,
    })
from openpyxl import Workbook
from django.http import HttpResponse

def export_jobs(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Jobs"

    ws.append(["Title", "Company", "Location"])

    for job in Job.objects.all():
        ws.append([job.title, job.company, job.location])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=jobs.xlsx'

    wb.save(response)
    return response
from django.core.exceptions import PermissionDenied

def recruiter_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != "recruiter":
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
@login_required
@recruiter_required
def recruiter_dashboard(request):
    jobs = Job.objects.filter(posted_by=request.user)
    return render(request, "recruiter_dashboard.html", {"jobs": jobs})
def login_redirect(request):
    if request.user.role == "admin":
        return redirect('admin_dashboard')
    elif request.user.role == "recruiter":
        return redirect('recruiter_dashboard')
    else:
        return redirect('home')
from django.shortcuts import render
from .models import Job

def job_list(request):
    jobs = Job.objects.filter(status='active').order_by('-created_at')

    context = {
        "jobs": jobs
    }

    return render(request, "jobs.html", context)  # ✅ FIXED
def job_apply(request):
    return render(request, 'jobs/apply.html')
def easy_apply(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == "POST":
        # your existing logic here
        pass

    return render(request, "apply.html", {"job": job})
from django.shortcuts import render

def companies(request):

    companies_list = [
        {
            "name": "Google",
            "desc": "Search, AI & Cloud technology leader",
            "type": "Product Company"
        },
        {
            "name": "Microsoft",
            "desc": "Cloud computing & enterprise software giant",
            "type": "Product Company"
        },
        {
            "name": "Amazon",
            "desc": "E-commerce, AWS cloud services",
            "type": "Product + Service"
        },
        {
            "name": "Meta",
            "desc": "Social media & VR technology company",
            "type": "Product Company"
        },
        {
            "name": "Netflix",
            "desc": "Global streaming entertainment platform",
            "type": "Media Tech"
        },
        {
            "name": "TCS",
            "desc": "IT services & consulting company (India)",
            "type": "Service Company"
        },
        {
            "name": "Infosys",
            "desc": "Software consulting & IT services",
            "type": "Service Company"
        },
        {
            "name": "Wipro",
            "desc": "Global IT solutions & consulting",
            "type": "Service Company"
        },
    ]

    return render(request, "jobs/companies.html", {
        "companies": companies_list,
        "total_companies": len(companies_list)
    })
def about(request):
    return render(request, "jobs/about.html")

def contact(request):
    return render(request, "jobs/contact.html")
from .models import ContactMessage
from django.core.mail import send_mail
from django.conf import settings
def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        ContactMessage.objects.create(
            name=name,
            email=email,
            message=message
        )

        # ✅ AUTO EMAIL REPLY (ADD HERE)
        send_mail(
            subject="We received your message",
            message="Thanks for contacting Job Portal. We will reply soon.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )

        return render(request, "jobs/contact.html", {
            "success": "Message sent successfully!"
        })

    return render(request, "jobs/contact.html")
from django.http import JsonResponse

def chatbot(request):
    if request.method == "POST":
        msg = request.POST.get("message")

        return JsonResponse({
            "reply": "I can help you with jobs, companies, and applications!"
        })

    return JsonResponse({"reply": "Invalid request"})
def reply_message(request, id):
    msg = get_object_or_404(SupportMessage, id=id)

    if request.method == "POST":
        msg.reply = request.POST.get("reply")
        msg.is_read = True
        msg.save()

        return redirect("admin_dashboard")

    return render(request, "reply.html", {"msg": msg})
def delete_message(request, id):
    msg = SupportMessage.objects.get(id=id)
    msg.delete()
    return redirect("admin_dashboard")
def mark_read(request, id):
    msg = SupportMessage.objects.get(id=id)
    msg.is_read = True
    msg.save()
    return redirect("admin_dashboard")
from django.shortcuts import get_object_or_404, redirect
from .models import SupportMessage

def support_reply(request, id):
    msg = get_object_or_404(SupportMessage, id=id)

    if request.method == "POST":
        msg.reply = request.POST.get("reply")
        msg.is_read = True
        msg.save()

    return redirect("admin_dashboard") 
from django.shortcuts import get_object_or_404, redirect
from .models import SupportMessage

from django.http import JsonResponse

def admin_reply(request, id):
    msg = get_object_or_404(SupportMessage, id=id)

    if request.method == "POST":
        reply_text = request.POST.get("reply")

        msg.reply = reply_text
        msg.is_read = True
        msg.save()

        return JsonResponse({"success": True, "message": "Reply sent"})

    return JsonResponse({"success": False, "error": "Invalid method"})
from django.http import JsonResponse
from .models import SupportMessage

def support_messages_api(request):
    msgs = SupportMessage.objects.select_related("user").order_by("-id")

    data = [
        {
            "id": m.id,
            "user": m.user.username,
            "message": m.message,
            "reply": m.reply or "",
            "is_read": m.is_read,
        }
        for m in msgs
    ]

    return JsonResponse({"messages": data})
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import SupportMessage

def mark_support_read(request, id):
    if request.method == "GET":
        msg = get_object_or_404(SupportMessage, id=id)
        msg.is_read = True
        msg.save()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid method"})

def support_api(request):
    msgs = SupportMessage.objects.select_related("user").order_by("-created_at")

    data = {
        "messages": [
            {
                "id": m.id,
                "user": m.user.username,
                "message": m.message,
                "is_read": m.is_read,
            }
            for m in msgs
        ]
    }

    return JsonResponse(data)
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import SupportMessage

def delete_support_message(request, id):
    if request.method == "POST":
        msg = get_object_or_404(SupportMessage, id=id)
        msg.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request"})
from django.http import JsonResponse
from .models import Application

def update_status(request, app_id, status):
    print("CALLED:", app_id, status)  # 👈 ADD THIS

    try:
        app = Application.objects.get(id=app_id)
        app.status = status
        app.save()
        return JsonResponse({"success": True})
    except Exception as e:
        print("ERROR:", e)
        return JsonResponse({"success": False})