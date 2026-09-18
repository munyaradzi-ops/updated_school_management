from django.shortcuts import render, redirect,get_object_or_404, redirect 
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from academic.models import Subject
from users.models import TeacherProfile

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from academic.models import Subject, Enrollment, Attendance, Grade  # Added Attendance and Grade here
from users.models import StudentProfile

from academic.models import Subject, Enrollment, Attendance, Grade, Invoice
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from users.models import User, TeacherProfile, StudentProfile
from academic.models import Classroom, Subject, Attendance


class CustomLoginView(auth_views.LoginView):
    """Custom login view that routes users based on their internal role."""
    template_name = 'registration/login.html'

@login_required
def dashboard_redirect(request):
    user = request.user
    if user.role == 'admin' or user.is_superuser:
        return redirect('admin_dashboard')
    elif user.role == 'teacher':
        return redirect('teacher_dashboard')
    elif user.role == 'student':
        return redirect('student_dashboard')
    elif user.role == 'parent':
        return redirect('parent_dashboard')  # Add this redirection link
    return redirect('login')


# --- PORTAL VIEWS ---

import json  # Add this import at the top of users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from users.models import User, TeacherProfile, StudentProfile
from academic.models import Classroom, Subject, Attendance, Invoice

@login_required
def admin_dashboard(request):
    """Aggregates metrics and structural chart parameters for the admin desk."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('dashboard_home')
        
    total_students = StudentProfile.objects.count()
    total_teachers = TeacherProfile.objects.count()
    total_classrooms = Classroom.objects.count()
    total_subjects = Subject.objects.count()
    
    recent_attendance = Attendance.objects.select_related('student__user', 'subject').order_by('-date')[:5]
    all_invoices = Invoice.objects.select_related('student__user').order_by('-due_date')[:5]

    # --- CHART LOGIC 1: DEMOGRAPHICS DATA AGGREGATION ---
    classrooms = Classroom.objects.all()
    classroom_labels = [c.name for c in classrooms]
    classroom_student_counts = [StudentProfile.objects.filter(current_class=c.name).count() for c in classrooms]

    # --- CHART LOGIC 2: FINANCIAL PERFORMANCE AGGREGATION ---
    invoices = Invoice.objects.all()
    total_due = sum(inv.amount_due for inv in invoices)
    total_paid = sum(inv.amount_paid for inv in invoices)
    total_outstanding = total_due - total_paid

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classrooms': total_classrooms,
        'total_subjects': total_subjects,
        'recent_attendance': recent_attendance,
        'all_invoices': all_invoices,
        
        # Pass JSON strings to context for easy JavaScript reading
        'classroom_labels': json.dumps(classroom_labels),
        'classroom_student_counts': json.dumps(classroom_student_counts),
        'financial_metrics': json.dumps([float(total_paid), float(total_outstanding)]),
    }
    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        return redirect('dashboard_home')
        
    # Get the teacher profile and find all subjects assigned to them
    teacher_profile = get_object_or_404(TeacherProfile, user=request.user)
    my_subjects = Subject.objects.filter(teacher=teacher_profile)
    from django.db import models
    announcements = Announcement.objects.filter(
        models.Q(target_classroom__in=[s.classroom for s in my_subjects]) | 
        models.Q(target_classroom__isnull=True)
    ).distinct().order_by('-date_posted')[:5]
    
    # Crucial step: 'announcements' must be explicitly passed into this context bundle
    return render(request, 'dashboards/teacher_dashboard.html', {
        'subjects': my_subjects, 
        'announcements': announcements
    })

@login_required
def student_dashboard(request):
    """Gathers data parameters specific to the logged-in student user."""
    if request.user.role != 'student':
        return redirect('dashboard_home')
        
    # Get the student's unique profile details
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    
    # 1. Find what classroom the student is actively enrolled in
    active_enrollment = Enrollment.objects.filter(student=student_profile, is_active=True).first()
    invoices = Invoice.objects.filter(student=student_profile).order_by('-due_date')
    
    my_subjects = []
    attendance_records = []
    grades = []
    attendance_percentage = 100.0

    if active_enrollment:
        # 2. Get all subjects taught in that classroom
        my_subjects = Subject.objects.filter(classroom=active_enrollment.classroom)
        
        # 3. Pull historical attendance logs for this student
        # FIND THIS LINE:
# attendance_records = Attendance.objects.filter(student=student_profile).order_range = '-date'

# AND REPLACE IT WITH THIS CORRECTED VERSION:
        attendance_records = Attendance.objects.filter(student=student_profile).order_by('-date')

        
        # Calculate overall attendance percentage metric
        total_days = attendance_records.count()
        if total_days > 0:
            days_present = attendance_records.filter(status__in=['Present', 'Late']).count()
            attendance_percentage = round((days_present / total_days) * 100, 1)
        else:
            attendance_percentage = "No logs recorded yet"
            
        # 4. Pull all grades/marks recorded for this student
        grades = Grade.objects.filter(student=student_profile).select_related('assessment__subject')
        from django.db import models
    announcements = Announcement.objects.filter(
        models.Q(target_classroom__in=[s.classroom for s in my_subjects]) | 
        models.Q(target_classroom__isnull=True)
    ).distinct().order_by('-date_posted')[:5]
    
    context = {
        'student_profile': student_profile,
        'classroom': active_enrollment.classroom if active_enrollment else None,
        'subjects': my_subjects,
        'attendance_records': attendance_records,
        'attendance_percentage': attendance_percentage,
        'grades': grades,
        'invoices': invoices, # Add this row
         'announcements': announcements
    }
    
    return render(request, 'dashboards/student_dashboard.html', context)


import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from users.models import StudentProfile
from academic.models import Invoice

@login_required
def export_student_roster_csv(request):
    """Generates a downloadable CSV containing the entire active student directory."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=401)

    # Setup the browser response header layout to trigger a file attachment download
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_roster_report.csv"'

    writer = csv.writer(response)
    # Write the column headers structure
    writer.writerow(['Roll Number', 'First Name', 'Last Name', 'Email', 'Classroom Section', 'Date of Birth'])

    # Fetch active students with related user authentication profiles efficiently
    students = StudentProfile.objects.select_related('user').all()
    for student in students:
        writer.writerow([
            student.roll_number,
            student.user.first_name,
            student.user.last_name,
            student.user.email,
            student.current_class,
            student.date_of_birth
        ])

    return response

@login_required
def export_fee_balances_csv(request):
    """Generates a downloadable CSV report of all invoices highlight outstanding balances."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=401)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="outstanding_fee_balances.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student Username', 'Invoice Title', 'Total Amount Due', 'Amount Paid', 'Balance Outstanding', 'Status'])

    invoices = Invoice.objects.select_related('student__user').all()
    for invoice in invoices:
        writer.writerow([
            invoice.student.user.username,
            invoice.title,
            invoice.amount_due,
            invoice.amount_paid,
            invoice.balance_outstanding,
            invoice.get_status_display()
        ])

    return response

    from academic.models import Subject, Enrollment, Attendance, Grade, Invoice
from users.models import ParentProfile

@login_required
def parent_dashboard(request):
    """Displays a parent's student dashboard tracking metrics for all linked children."""
    if request.user.role != 'parent':
        return redirect('dashboard_home')

    parent = get_object_or_404(ParentProfile, user=request.user)
    linked_children = parent.students.all()

    # If the parent clicks on a specific child, load that child's data
    selected_student_id = request.GET.get('student_id')
    selected_child = None
    child_data = {}

    if selected_student_id:
        selected_child = get_object_or_404(StudentProfile, user_id=selected_student_id, parents=parent)
    elif linked_children.exists():
        # Default to the first child if none is selected
        selected_child = linked_children.first()

    if selected_child:
        active_enrollment = Enrollment.objects.filter(student=selected_child, is_active=True).first()
        attendance_records = Attendance.objects.filter(student=selected_child).order_by('-date')
        
        # Calculate attendance percentage metric
        total_days = attendance_records.count()
        attendance_percentage = 100.0
        if total_days > 0:
            days_present = attendance_records.filter(status__in=['Present', 'Late']).count()
            attendance_percentage = round((days_present / total_days) * 100, 1)
        else:
            attendance_percentage = "No logs recorded"

        child_data = {
            'classroom': active_enrollment.classroom if active_enrollment else None,
            'subjects': Subject.objects.filter(classroom=active_enrollment.classroom) if active_enrollment else [],
            'grades': Grade.objects.filter(student=selected_child).select_related('assessment__subject'),
            'invoices': Invoice.objects.filter(student=selected_child).order_by('-due_date'),
            'attendance_percentage': attendance_percentage,
            'attendance_records': attendance_records[:10], # Last 10 days log
        }

    context = {
        'linked_children': linked_children,
        'selected_child': selected_child,
        'child_data': child_data,
    }
    return render(request, 'dashboards/parent_dashboard.html', context)

from django.contrib import messages
from academic.models import Announcement

@login_required
def admin_post_announcement(request):
    """Allows administrators to post system-wide notices directly from the frontend panel."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('dashboard_home')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')

        if title and content:
            Announcement.objects.create(
                title=title,
                content=content,
                author=request.user,
                target_classroom=None  # Broadcasts to the entire school
            )
            messages.success(request, f"Global notice '{title}' has been successfully broadcast.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Please fill out both the title and content fields.")

    return render(request, 'academic/admin_post_announcement.html')

