from django.urls import path
from . import views

urlpatterns = [

    # AUTH
    path('', views.login_view, name='login'),
    path('login/', views.login_view),
    path('signup/', views.signup_view),
    path('logout/', views.logout_view),

    # HOME
    path('home/', views.home),

    # JOBS
    path('jobs/', views.job_list),
    path('apply/<int:job_id>/', views.apply_job),

    # USER
    path('profile/', views.profile),
   path('settings/', views.user_settings, name='user_settings'),
    path('support/', views.support),
    path('my-applications/', views.my_applications),

    # RECRUITER
    path('post-job/', views.post_job),
    path('recruiter-dashboard/', views.recruiter_dashboard),
    path('update-status/<int:app_id>/<str:status>/', views.update_status),

    # CHAT / DASHBOARD
    path('dashboard/', views.dashboard),
    path('create-post/', views.create_post),
    path('chat/', views.chat),
    path('send-message/', views.send_message),

    # OTP
    path('send-otp/', views.send_otp),
    path('verify-otp/', views.verify_otp),

    # ADMIN
    path('admin-dashboard/', views.admin_dashboard),
    path('dashboard/users/', views.admin_users, name='admin_users'),
path("dashboard/jobs/", views.admin_jobs, name="admin_jobs"),
path('dashboard/jobs/edit/<int:job_id>/', views.edit_job, name='edit_job'),
path('jobs/', views.job_list, name='job_list'),

path('dashboard/jobs/delete/<int:job_id>/', views.delete_job, name='delete_job'),
path('dashboard/applications/', views.admin_applications, name='admin_applications'),
path("update-status/", views.update_application_status, name="update_status"),
    path('admin-post-job/', views.admin_post_job, name='admin_post_job'),
    path('dashboard/export-jobs/', views.export_jobs, name='export_jobs'),
   path('dashboard/jobs/delete/<int:job_id>/', views.delete_job, name='delete_job'),
]