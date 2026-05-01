from django.urls import path
from . import views

urlpatterns = [
    # 🔐 AUTH (MISSING PART - FIXED)
    path('', views.login_view, name='login'),   # important
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view),
    path('logout/', views.logout_view),

    # 🏠 HOME
    path('home/', views.home, name='home'),

    # JOBS
    path('jobs/', views.job_list),
    path('apply/<int:job_id>/', views.apply_job),

    # USER
    path('profile/', views.profile),
    path('settings/', views.settings),
    path('support/', views.support),
    path('my-applications/', views.my_applications),

    # RECRUITER
    path('post-job/', views.post_job),
    path('recruiter-dashboard/', views.recruiter_dashboard),
    path('update-status/<int:app_id>/<str:status>/', views.update_status),

    # ADMIN / DASHBOARD
    path('admin-dashboard/', views.admin_dashboard),
    path('dashboard/', views.dashboard),

    # EXTRA
    path('create-post/', views.create_post),
    path('chat/', views.chat),
    path('send-message/', views.send_message),
    path('send-otp/', views.send_otp),
path('verify-otp/', views.verify_otp),
path('admin-post-job/', views.admin_post_job, name='admin_post_job'),
path('admin-reply/<int:id>/', views.admin_reply),
]