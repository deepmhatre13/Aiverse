from rest_framework import serializers
from .models import ActivityEvent, PerformanceSnapshot


class ActivityEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = ActivityEvent
        fields = [
            'id',
            'event_type',
            'event_type_display',
            'reference_id',
            'score_delta',
            'metadata',
            'created_at'
        ]
        read_only_fields = fields


class PerformanceSnapshotSerializer(serializers.ModelSerializer):
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceSnapshot
        fields = [
            'id',
            'date',
            'problems_attempted',
            'problems_solved',
            'avg_score',
            'streak_day',
            'success_rate'
        ]
        read_only_fields = fields
    
    def get_success_rate(self, obj):
        if obj.problems_attempted > 0:
            return round((obj.problems_solved / obj.problems_attempted) * 100, 2)
        return 0.0