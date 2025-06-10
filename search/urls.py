from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('search/', views.job_search, name='job_search'),
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('my-applications/', views.my_applications, name='my_applications'),
] 