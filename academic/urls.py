from django.urls import path
from . import views

# Add this single line to register the namespace!
app_name = 'academic'

urlpatterns = [
    path('attendance/take/<int:subject_id>/', views.take_attendance, name='take_attendance'),
    path('assessment/create/<int:subject_id>/', views.create_assessment, name='create_assessment'),
    path('assessment/marks/<int:assessment_id>/', views.enter_marks, name='enter_marks'),
     path('announcement/new/<int:subject_id>/', views.post_announcement, name='post_announcement'),
         # New Admin Frontend Payment Route
    path('invoice/record-payment/<int:invoice_id>/', views.admin_record_payment, name='admin_record_payment'),

]
