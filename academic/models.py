from django.db import models
from users.models import TeacherProfile, StudentProfile
# Add this line at the very top of academic/models.py with your other imports
from django.conf import settings




class Classroom(models.Model):
    """Represents a distinct class section, e.g., Grade 10-A, Grade 11-B."""
    name = models.CharField(max_length=50, unique=True)
    section = models.CharField(max_length=10, blank=True)
    room_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name

class Subject(models.Model):
    """Represents a course of study taught in the school."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True) # e.g., MATH101
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='subjects')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_subjects')

    def __str__(self):
        return f"{self.name} ({self.classroom.name})"

class Enrollment(models.Model):
    """Links a student to a specific classroom for an academic tracking period."""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='enrolled_students')
    date_enrolled = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'classroom') # Prevents registering a student to the same class twice

    def __str__(self):
        return f"{self.student.user.get_full_name() or self.student.user.username} in {self.classroom.name}"


class Attendance(models.Model):
    """Stores the daily attendance status for a student in a specific course."""
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance_records')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendance_logs')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    remarks = models.CharField(max_length=255, blank=True, null=True) # e.g., "Sick leave note submitted"

    class Meta:
        unique_together = ('student', 'subject', 'date') # Prevents duplicate logs for the same day

    def __str__(self):
        return f"{self.student} - {self.subject.name} - {self.date}: {self.status}"

from django.core.validators import MinValueValidator, MaxValueValidator

class Assessment(models.Model):
    """Represents a graded item like an assignment, exam, or quiz."""
    TYPE_CHOICES = [
        ('Assignment', 'Assignment'),
        ('Quiz', 'Quiz'),
        ('Midterm', 'Midterm Exam'),
        ('Final', 'Final Exam'),
    ]
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assessments')
    name = models.CharField(max_length=100) # e.g., "Algebra Quiz 1"
    assessment_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    max_marks = models.PositiveIntegerField(default=100)
    date_issued = models.DateField()

    def __str__(self):
        return f"{self.name} - {self.subject.name} (Max: {self.max_marks})"

class Grade(models.Model):
    """Stores the specific marks achieved by a student for a particular assessment."""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='grades')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='student_marks')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('student', 'assessment') # A student can only have one grade record per assessment

    def __str__(self):
        return f"{self.student} - {self.assessment.name}: {self.marks_obtained}/{self.assessment.max_marks}"


class Invoice(models.Model):
    """Represents a financial bill issued to a student for tuition or school utilities."""
    STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Partially_Paid', 'Partially Paid'),
        ('Paid', 'Paid'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='invoices')
    title = models.CharField(max_length=150) # e.g., "Term 1 Tuition Fees"
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Unpaid')
    date_issued = models.DateField(auto_now_add=True)
    due_date = models.DateField()

    @property
    def balance_outstanding(self):
        """Calculates the dynamic balance remaining on this specific invoice."""
        return self.amount_due - self.amount_paid

    def __str__(self):
        return f"{self.title} - {self.student.user.username} (${self.balance_outstanding} left)"


class Payment(models.Model):
    """Stores verified institutional transaction history logs handled by administration."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount_tendered = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    reference_number = models.CharField(max_length=100, unique=True) # Bank deposit slip ID or receipt code

    def save(self, *args, **kwargs):
        """Overrides save method to instantly compute and update the parent invoice statuses."""
        super().save(*args, **kwargs)
        
        invoice = self.invoice
        # Directly sum all administrative logged rows
        total_payments = sum(p.amount_tendered for p in invoice.payments.all())
        invoice.amount_paid = total_payments
        
        if invoice.amount_paid >= invoice.amount_due:
            invoice.status = 'Paid'
        elif invoice.amount_paid > 0:
            invoice.status = 'Partially_Paid'
        else:
            invoice.status = 'Unpaid'
        invoice.save()

    def __str__(self):
        return f"Payment of ${self.amount_tendered} for Invoice #{self.invoice.id}"


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    
    # CHANGE THIS LINE FROM: models.ForeignKey(User, ...)
    # TO THIS:
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='announcements')
    
    target_classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')

    def __str__(self):
        target = self.target_classroom.name if self.target_classroom else "All School"
        return f"{self.title} ({target}) - {self.date_posted.strftime('%d %b %Y')}"
from django.utils import timezone
from .models import Subject, Announcement # Ensure Announcement is included in your imports


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
            messages.error(request, "Please fill out both the title and content fields.")

    return render(request, 'academic/post_announcement.html', {'subject': subject})

