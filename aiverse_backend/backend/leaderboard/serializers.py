from rest_framework import serializers
from .models import LeaderboardEntry, LeaderboardEvent


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = LeaderboardEntry
        fields = [
            'id',
            'username',
            'email',
            'total_points',
            'problems_solved',
            'avg_score',
            'streak_days',
            'rank',
            'updated_at'
        ]
        read_only_fields = fields


class LeaderboardEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = LeaderboardEvent
        fields = [
            'id',
            'event_type',
            'event_type_display',
            'points_delta',
            'metadata',
            'created_at'
        ]
        read_only_fields = fields