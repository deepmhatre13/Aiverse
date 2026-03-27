"""
Django Admin Configuration for Learn Module.

Updated to match production-grade models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Course, Lesson, Enrollment, LessonProgress, 
    Certificate, CourseRating, Payment,
    CourseAnalytics, LessonAnalytics
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'level', 'is_free', 'price', 'is_published', 'students_count', 'created_at']
    list_filter = ['is_free', 'is_published', 'level', 'track']
    search_fields = ['title', 'slug', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'total_lessons', 'total_duration_minutes', 
                       'rating_average', 'rating_count', 'students_count', 'completion_rate']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description', 'thumbnail')
        }),
        ('Classification', {
            'fields': ('level', 'estimated_duration_hours', 'track', 'required_rating')
        }),
        ('Pricing', {
            'fields': ('is_free', 'is_paid', 'price', 'currency')
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_at')
        }),
        ('Statistics (Read-only)', {
            'fields': ('total_lessons', 'total_duration_minutes', 'rating_average', 
                       'rating_count', 'students_count', 'completion_rate'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ['order', 'title', 'slug', 'duration_minutes', 'is_preview']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'duration_minutes', 'video_type', 'is_preview']
    list_filter = ['course', 'video_type', 'is_preview']
    search_fields = ['title', 'course__title']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'section', 'title', 'slug', 'description', 'content')
        }),
        ('Video', {
            'fields': ('video_type', 'youtube_id', 'hosted_video_url', 'duration_minutes')
        }),
        ('Access Control', {
            'fields': ('is_preview', 'order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'status', 'completion_percentage', 'enrolled_at', 'activated_at']
    list_filter = ['status', 'course', 'is_paid', 'enrolled_at']
    search_fields = ['user__email', 'course__title', 'payment_reference']
    readonly_fields = ['enrolled_at', 'payment_reference', 'completion_percentage', 'lessons_completed']
    
    fieldsets = (
        ('Enrollment Info', {
            'fields': ('user', 'course', 'status')
        }),
        ('Payment', {
            'fields': ('is_paid', 'payment_reference', 'amount_paid')
        }),
        ('Progress', {
            'fields': ('completion_percentage', 'lessons_completed', 'certificate_issued', 'certificate_issued_at')
        }),
        ('Timestamps', {
            'fields': ('enrolled_at', 'purchased_at', 'activated_at', 'last_accessed_at', 'expires_at')
        }),
    )


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'is_completed', 'watch_time_display', 'last_watched_at']
    list_filter = ['is_completed', 'lesson__course']
    search_fields = ['user__email', 'lesson__title']
    readonly_fields = ['first_watched_at', 'last_watched_at', 'completed_at']
    
    def watch_time_display(self, obj):
        minutes = obj.watch_time_seconds // 60
        seconds = obj.watch_time_seconds % 60
        return f"{minutes}m {seconds}s"
    watch_time_display.short_description = 'Watch Time'
    
    fieldsets = (
        ('Progress Info', {
            'fields': ('user', 'lesson', 'enrollment')
        }),
        ('Progress Details', {
            'fields': ('is_completed', 'watch_time_seconds', 'last_position_seconds')
        }),
        ('Timestamps', {
            'fields': ('first_watched_at', 'completed_at', 'last_watched_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_id', 'user', 'course', 'issued_at']
    list_filter = ['course', 'issued_at']
    search_fields = ['certificate_id', 'user__email', 'course__title']
    readonly_fields = ['certificate_id', 'issued_at', 'pdf_url', 'qr_code_url']
    
    fieldsets = (
        ('Certificate Info', {
            'fields': ('certificate_id', 'user', 'course', 'enrollment')
        }),
        ('Files', {
            'fields': ('pdf_url', 'qr_code_url')
        }),
        ('Metadata', {
            'fields': ('issued_at',)
        }),
    )


@admin.register(CourseRating)
class CourseRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'rating_display', 'created_at']
    list_filter = ['rating', 'course', 'created_at']
    search_fields = ['user__email', 'course__title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    
    def rating_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #f59e0b;">{}</span>', stars)
    rating_display.short_description = 'Rating'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'enrollment', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['user__email', 'stripe_payment_intent_id', 'stripe_checkout_session_id']
    readonly_fields = ['stripe_payment_intent_id', 'stripe_checkout_session_id', 'created_at', 'succeeded_at']
    
    fieldsets = (
        ('Payment Info', {
            'fields': ('user', 'enrollment', 'amount', 'currency', 'status')
        }),
        ('Stripe', {
            'fields': ('stripe_payment_intent_id', 'stripe_checkout_session_id', 'stripe_charge_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'succeeded_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CourseAnalytics)
class CourseAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['course', 'date', 'enrollments', 'completions', 'revenue']
    list_filter = ['course', 'date']
    date_hierarchy = 'date'
    ordering = ['-date']


@admin.register(LessonAnalytics)
class LessonAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'date', 'views', 'completions', 'avg_watch_time']
    list_filter = ['lesson__course', 'date']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    def avg_watch_time(self, obj):
        minutes = obj.average_watch_time_seconds // 60
        return f"{minutes}m"
    avg_watch_time.short_description = 'Avg Watch Time'
