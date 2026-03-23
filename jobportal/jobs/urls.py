from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('jobs/', views.job_list),
    path('apply/<int:job_id>/', views.apply_job),

    path('login/', views.login_view),
    path('signup/', views.signup_view),
    path('dashboard/', views.dashboard),
    path('post-job/', views.post_job),
]