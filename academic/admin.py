from django.contrib import admin
from .models import Classroom, Subject, Enrollment
from .models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'target_classroom', 'date_posted')
    list_filter = ('target_classroom', 'date_posted')
    search_fields = ('title', 'content')


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'room_number')
    search_fields = ('name',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'classroom', 'teacher')
    list_filter = ('classroom', 'teacher')
    search_fields = ('name', 'code')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'classroom', 'date_enrolled', 'is_active')
    list_filter = ('classroom', 'is_active')

from django.contrib import admin
from .models import Classroom, Subject, Enrollment, Attendance, Assessment, Grade, Invoice, Payment

# Inline configuration to see payment logs inside the invoice screen
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'amount_due', 'amount_paid', 'status', 'due_date')
    list_filter = ('status', 'due_date')
    search_fields = ('student__user__username', 'title')
    inlines = [PaymentInline]

admin.site.register(Payment)
