from django.shortcuts import render, get_object_or_404, redirect
from .models import Job, Application, User

# Django Auth
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User as AuthUser
from django.contrib import messages


# 🏠 Home Page
def home(request):
    jobs = Job.objects.all()[:6]

    companies = Job.objects.values_list('company', flat=True).distinct()

    return render(request, 'home.html', {
        'jobs': jobs,
        'companies': companies
    })


# 📄 Job List
def job_list(request):
    query = request.GET.get('q')
    location = request.GET.get('location')

    jobs = Job.objects.all()

    if query:
        jobs = jobs.filter(title__icontains=query)

    if location:
        jobs = jobs.filter(location__icontains=location)

    return render(request, 'jobs.html', {'jobs': jobs})

# 📨 Apply Job
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        linkedin = request.POST.get('linkedin')
        resume = request.FILES.get('resume')

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'name': name,
                'password': '1234',
                'role': 'jobseeker'
            }
        )

        Application.objects.create(
            user=user,
            job=job,
            resume=resume,
            linkedin=linkedin
        )

        messages.success(request, "Applied successfully!")
        return redirect('/jobs/')

    return render(request, 'apply.html', {'job': job})


# 🔐 Signup (FIXED ✅)
def signup_view(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')

        # ✅ Check duplicate user
        if AuthUser.objects.filter(username=email).exists():
            messages.error(request, "Email already registered. Please login.")
            return redirect('/signup/')

        # ✅ Create Django auth user
        auth_user = AuthUser.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        # ✅ Create custom user
        User.objects.create(
            name=name,
            email=email,
            password=password,
            role=role
        )

        messages.success(request, "Account created successfully!")
        return redirect('/login/')

    return render(request, 'signup.html')


# 🔑 Login
def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('/dashboard/')
        else:
            messages.error(request, "Invalid Credentials")
            return redirect('/login/')

    return render(request, 'login.html')


# 🚪 Logout
def logout_view(request):
    logout(request)
    return redirect('/')


# 📊 Dashboard
def dashboard(request):
    return render(request, 'dashboard.html')


# 📝 Post Job (Recruiter)
from django.contrib.auth.decorators import login_required
from .models import User, Job

@login_required
def post_job(request):
    if request.method == "POST":
        title = request.POST.get('title')
        company = request.POST.get('company')
        location = request.POST.get('location')
        description = request.POST.get('description')

        # Get the custom User instance for the logged-in auth user
        custom_user = User.objects.get(email=request.user.email)

        # Create job
        Job.objects.create(
            title=title,
            company=company,
            location=location,
            description=description,
            posted_by=custom_user  # now correct
        )

        messages.success(request, "Job posted successfully!")
        return redirect('/jobs/')

    return render(request, 'post_job.html')
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    custom_user = User.objects.get(email=request.user.email)
    applications = Application.objects.filter(user=custom_user)

    return render(request, 'dashboard.html', {'applications': applications})
def home(request):
    jobs = Job.objects.all()[:6]

    companies = Job.objects.values_list('company', flat=True).distinct()

    return render(request, 'home.html', {
        'jobs': jobs,
        'companies': companies
    })