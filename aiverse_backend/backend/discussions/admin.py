from django.contrib import admin
from .models import Category, Thread, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'category',
        'created_by',
        'post_count',
        'last_post_at',
        'created_at',
    ]
    list_filter = ['category', 'created_at', 'last_post_at']
    search_fields = ['title', 'created_by__email']
    readonly_fields = ['created_at', 'post_count', 'last_post_at']
    
    fieldsets = (
        ('Thread Info', {
            'fields': ('title', 'category', 'created_by')
        }),
        ('Stats', {
            'fields': ('post_count', 'last_post_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'thread', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['created_by__email', 'content', 'thread__title']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Post Info', {
            'fields': ('thread', 'created_by', 'content')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    