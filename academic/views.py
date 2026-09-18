from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date
# FIND your academic models import line at the top of academic/views.py and update it to:
from .models import Subject, Enrollment, Attendance, Assessment, Grade, Announcement  # Ensure Announcement is here!

# Also ensure your users app models are imported correctly right below it:
from users.models import TeacherProfile

from users.models import TeacherProfile

@login_required
def take_attendance(request, subject_id):
    """Allows a teacher to view the roster and mark attendance for a specific subject."""
    # Ensure the user is a teacher and has a profile
    if request.user.role != 'teacher':
        return redirect('dashboard_home')
        
    teacher_profile = get_object_or_404(TeacherProfile, user=request.user)
    # Fetch the subject ensuring it belongs to the logged in teacher
    subject = get_object_or_404(Subject, id=subject_id, teacher=teacher_profile)
    
    # Get all students enrolled in the classroom associated with this subject
    enrolled_students = Enrollment.objects.filter(classroom=subject.classroom, is_active=True)
    
    # Use today's date
    today = date.today()

    if request.method == 'POST':
        # Process the form data when the teacher clicks save
        for enrollment in enrolled_students:
            student_id = enrollment.student.user.id
            # Retrieve the status submitted for each student from the dropdown/radio buttons
            status = request.POST.get(f'status_{student_id}', 'Present')
            remarks = request.POST.get(f'remarks_{student_id}', '')

            # Create or update the attendance entry for today
            Attendance.objects.update_or_create(
                student=enrollment.student,
                subject=subject,
                date=today,
                defaults={'status': status, 'remarks': remarks}
            )
            
        messages.success(request, f"Attendance for {subject.name} successfully saved for {today}.")
        return redirect('teacher_dashboard')

    context = {
        'subject': subject,
        'enrolled_students': enrolled_students,
        'today': today,
    }
    return render(request, 'academic/take_attendance.html', context)

# Add this import at the top of academic/views.py alongside your other models
from .models import Subject, Enrollment, Attendance, Assessment, Grade

@login_required
def create_assessment(request, subject_id):
    """Allows a teacher to create a new graded assignment or exam."""
    if request.user.role != 'teacher':
        return redirect('dashboard_home')
        
    teacher_profile = get_object_or_404(TeacherProfile, user=request.user)
    subject = get_object_or_404(Subject, id=subject_id, teacher=teacher_profile)

    if request.method == 'POST':
        name = request.POST.get('name')
        assessment_type = request.POST.get('assessment_type')
        max_marks = request.POST.get('max_marks')
        date_issued = request.POST.get('date_issued')

        # This block only executes when the form is submitted via POST
        assessment = Assessment.objects.create(
            subject=subject,
            name=name,
            assessment_type=assessment_type,
            max_marks=max_marks,
            date_issued=date_issued
        )
        messages.success(request, f"Assessment '{name}' successfully created.")
        return redirect('academic:enter_marks', assessment_id=assessment.id)

    # Make absolutely sure this line is aligned to the far left block of the function!
    # It handles the regular GET request to display the initial empty form.
    return render(request, 'academic/create_assessment.html', {'subject': subject})

@login_required
def enter_marks(request, assessment_id):
    """Allows a teacher to batch-input scores for all students enrolled in the class."""
    if request.user.role != 'teacher':
        return redirect('dashboard_home')

    teacher_profile = get_object_or_404(TeacherProfile, user=request.user)
    assessment = get_object_or_404(Assessment, id=assessment_id, subject__teacher=teacher_profile)
    enrolled_students = Enrollment.objects.filter(classroom=assessment.subject.classroom, is_active=True)

    if request.method == 'POST':
        for enrollment in enrolled_students:
            student_id = enrollment.student.user.id
            score = request.POST.get(f'marks_{student_id}')
            remarks = request.POST.get(f'remarks_{student_id}', '')

            if score: # Only save if a grade value was provided
                Grade.objects.update_or_create(
                    student=enrollment.student,
                    assessment=assessment,
                    defaults={'marks_obtained': score, 'remarks': remarks}
                )

        messages.success(request, f"Grades saved successfully for {assessment.name}.")
        return redirect('teacher_dashboard')

    # Fetch existing grades to prepopulate inputs if they already exist
    existing_grades = {g.student_id: g.marks_obtained for g in Grade.objects.filter(assessment=assessment)}

    context = {
        'assessment': assessment,
        'enrolled_students': enrolled_students,
        'existing_grades': existing_grades,
    }
    return render(request, 'academic/enter_marks.html', context)

# Make sure this exact function name exists at the bottom of academic/views.py
@login_required
def post_announcement(request, subject_id):
    """Allows a teacher to post an announcement directly to a classroom broadcast stream."""
    if request.user.role != 'teacher':
        return redirect('dashboard_home')
        
    teacher_profile = get_object_or_404(TeacherProfile, user=request.user)
    subject = get_object_or_404(Subject, id=subject_id, teacher=teacher_profile)

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')

        if title and content:
            Announcement.objects.create(
                title=title,
                content=content,
                author=request.user,
                target_classroom=subject.classroom
            )
            messages.success(request, f"Notice '{title}' successfully broadcast to {subject.classroom.name}.")
            return redirect('teacher_dashboard')
        else:
            messages.error(request, "Please fill out both fields.")

    return render(request, 'academic/post_announcement.html', {'subject': subject})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Invoice, Payment

@login_required
def admin_record_payment(request, invoice_id):
    """Allows administrators to log a transaction against a student invoice from the frontend."""
    # Strict role security check
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('dashboard_home')

    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == 'POST':
        amount = request.POST.get('amount_tendered')
        reference = request.POST.get('reference_number')

        if amount and reference:
            # Create the payment log row
            Payment.objects.create(
                invoice=invoice,
                amount_tendered=amount,
                reference_number=reference
            )
            messages.success(request, f"Successfully logged payment of ${amount} for Invoice #{invoice.id}.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Please fill out all required transaction parameters.")

    return render(request, 'academic/admin_record_payment.html', {'invoice': invoice})
