from django.contrib import admin
from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'recommendation_type', 'content_type', 'score', 'is_dismissed')
    list_filter = ('recommendation_type', 'source', 'is_dismissed')
    search_fields = ('user__username',)
    readonly_fields = ('generated_at',)
