# from django.contrib import admin
# from .models import Course, Group, VideoLesson, Task, Assistant_Teacher, High_Teacher
#
# admin.site.register(Course)
# admin.site.register(Group)
# admin.site.register(High_Teacher)
# admin.site.register(Assistant_Teacher)
# admin.site.register(VideoLesson)
# admin.site.register(Task)
#
#

from django.contrib import admin
from .models import Course, Group, VideoLesson, Task, Assistant_Teacher, High_Teacher
from student.models import Student

# ================== Student Inline ==================
class StudentInline(admin.TabularInline):
    model = Student
    fk_name = 'assigned_group'  # qaysi field bilan Group bog‘langan
    extra = 0
    readonly_fields = ['full_name', 'phone_number', 'email']
    show_change_link = True  # talaba profiliga tez kirish

# ================== Group Admin ==================
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'main_teacher', 'is_active']
    search_fields = ['name', 'course__name', 'main_teacher__full_name']
    list_filter = ['course', 'is_active']
    filter_horizontal = ['assistant_teacher']  # yordamchi ustozlar qulay tanlanadi
    inlines = [StudentInline]  # guruhdagi talabalar inline ko‘rinadi

# ================== Group Inline for Course ==================
class GroupInline(admin.TabularInline):
    model = Group
    fk_name = 'course'  # group qaysi kursga tegishli
    extra = 0
    readonly_fields = ['name', 'main_teacher', 'is_active']
    show_change_link = True  # guruh paneliga tez kirish

# ================== Course Admin ==================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['is_active']
    inlines = [GroupInline]  # kursga biriktirilgan guruhlar inline ko‘rinadi

# ================== High Teacher Admin ==================
@admin.register(High_Teacher)
class HighTeacherAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone_number', 'email', 'job', 'experience_year']
    search_fields = ['full_name', 'phone_number', 'email']

# ================== Assistant Teacher Admin ==================
@admin.register(Assistant_Teacher)
class AssistantTeacherAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone_number', 'email', 'job', 'experience_year']
    search_fields = ['full_name', 'phone_number', 'email']

# ================== Video Lesson Admin ==================
@admin.register(VideoLesson)
class VideoLessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'uploaded_by', 'created_at']
    search_fields = ['title', 'description']
    filter_horizontal = ['course', 'group']  # qaysi kurs va guruhga tegishli

# ================== Task Admin ==================
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'video_lesson', 'student', 'assistant_teacher', 'score', 'created_at']
    search_fields = ['student__full_name', 'video_lesson__title']
    list_filter = ['assistant_teacher', 'score']
