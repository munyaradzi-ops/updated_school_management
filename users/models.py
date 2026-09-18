from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    IS_ADMIN = 'admin'
    IS_TEACHER = 'teacher'
    IS_STUDENT = 'student'
    IS_PARENT = 'parent'  # Add this row
    
    ROLE_CHOICES = [
        (IS_ADMIN, 'Admin'),
        (IS_TEACHER, 'Teacher'),
        (IS_STUDENT, 'Student'),
        (IS_PARENT, 'Parent'),  # Add this row
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=IS_STUDENT)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='admin_profile')
    management_level = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Admin: {self.user.username}"

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='teacher_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"Teacher: {self.user.get_full_name() or self.user.username}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='student_profile')
    roll_number = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    current_class = models.CharField(max_length=50, blank=True) # e.g., "Grade 10-A"

    def __str__(self):
        return f"Student: {self.user.get_full_name() or self.user.username}"

class ParentProfile(models.Model):
    """Profile specifically for parents, linked to one or more students."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='parent_profile')
    students = models.ManyToManyField(StudentProfile, related_name='parents', blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"Parent: {self.user.get_full_name() or self.user.username}"
