from django.urls import path
from . import views

urlpatterns = [

    # ================= AUTH =================
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login_page'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # ================= HOME =================
    path('home/', views.home, name='home'),

    # ================= JOBS =================
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('easy-apply/<int:job_id>/', views.easy_apply, name='easy_apply'),

    # ================= USER =================
    path('profile/', views.profile, name='profile'),
    path('settings/', views.user_settings, name='user_settings'),
    path('support/', views.support, name='support'),
    path('my-applications/', views.my_applications, name='my_applications'),

    # ================= RECRUITER =================
    path('post-job/', views.admin_post_job, name='post_job'),
    path('recruiter-dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('update-status/<int:app_id>/<str:status>/', views.update_status, name='update_status'),

    # ================= DASHBOARD =================
    path('dashboard/', views.dashboard, name='dashboard'),

    # FIXED (comma added)
    path('dashboard/post-job/', views.admin_post_job, name='admin_post_job'),
    path('create-post/', views.create_post, name='create_post'),

    path('chat/', views.chat, name='chat'),
    path('send-message/', views.send_message, name='send_message'),

    # ================= OTP =================
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    # ================= ADMIN DASHBOARD =================
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('dashboard/users/', views.admin_users, name='admin_users'),
    path('dashboard/jobs/', views.admin_jobs, name='admin_jobs'),
    path('dashboard/jobs/edit/<int:job_id>/', views.edit_job, name='edit_job'),
    path('dashboard/jobs/delete/<int:job_id>/', views.delete_job, name='delete_job'),
    path('dashboard/applications/', views.admin_applications, name='admin_applications'),

    path('dashboard/export-jobs/', views.export_jobs, name='export_jobs'),

    # ================= STATIC =================
    path('companies/', views.companies, name='companies'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # ================= CHATBOT =================
    path('chatbot/', views.chatbot, name='chatbot'),

    # ================= SUPPORT API =================
    path('api/support/', views.support_api, name='support_api'),
    path('support/read/<int:id>/', views.mark_support_read, name='support_read'),
    path('support/delete/<int:id>/', views.delete_support_message, name='delete_support_message'),
    path('support/admin-reply/<int:id>/', views.admin_reply, name='admin_reply'),
    path('update-status/<int:app_id>/<str:status>/', views.update_status)
]