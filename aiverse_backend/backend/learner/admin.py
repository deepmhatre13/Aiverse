from django.contrib import admin
from .models import ConceptMastery, LearnerProfile, LearningPath


@admin.register(ConceptMastery)
class ConceptMasteryAdmin(admin.ModelAdmin):
    list_display = ('user', 'concept_tag', 'mastery_score', 'is_struggling')
    list_filter = ('concept_tag', 'is_struggling')
    search_fields = ('user__username',)


@admin.register(LearnerProfile)
class LearnerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'estimated_skill_level', 'overall_mastery', 'engagement_score')
    list_filter = ('estimated_skill_level',)
    search_fields = ('user__username',)


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_adaptive', 'generated_at')
    list_filter = ('is_adaptive',)
    search_fields = ('user__username',)
