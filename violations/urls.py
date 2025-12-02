from django.urls import path
from . import views

urlpatterns = [
    path('', views.MainView.as_view(), name='main'),
    path('api/video/upload/', views.VideoUploadView.as_view(), name='video_upload'),
    path('api/violations/', views.ViolationsListView.as_view(), name='violations_list'),
    path('api/violations/<str:video_id>/', views.VideoViolationsView.as_view(), name='violations_video'),
    path('api/video/progress/<str:video_id>/', views.VideoProgressView.as_view(), name='video_progress'),
    path('api/video/<str:video_id>/', views.VideoView.as_view(), name='video_get'),
    path('api/tasks/', views.TaskStatusView.as_view(), name='tasks_status'),
    path('api/tasks/<str:video_id>/complete/', views.TaskCompleteView.as_view(), name='task_complete'),
    path('report/', views.ReportView.as_view(), name='report'),
    path('report/export/', views.ExportExcelView.as_view(), name='export_excel'),
    path('export-excel/', views.ExportExcelView.as_view(), name='export_excel_alt'),
]

