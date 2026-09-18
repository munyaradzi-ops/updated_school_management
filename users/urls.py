from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Map the completely empty root URL path directly to our dashboard redirect logic
    path('', views.dashboard_redirect, name='home_redirect'), 
    
    # Auth Routes
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Redirection Engine
    path('dashboard/', views.dashboard_redirect, name='dashboard_home'),
    
    # Dedicated Portals
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    
     path('dashboard/admin/report/students/', views.export_student_roster_csv, name='report_students'),
    path('dashboard/admin/report/balances/', views.export_fee_balances_csv, name='report_balances'),
        path('dashboard/parent/', views.parent_dashboard, name='parent_dashboard'),
    # New Admin Announcement Path
    path('dashboard/admin/announcement/new/', views.admin_post_announcement, name='admin_post_announcement'),

]
