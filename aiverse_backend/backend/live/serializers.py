from rest_framework import serializers
from .models import LiveSession, LiveRegistration


class LiveSessionSerializer(serializers.ModelSerializer):
    host_username = serializers.CharField(source='host.username', read_only=True)
    host_display_name = serializers.CharField(source='host.display_name', read_only=True)
    is_registered = serializers.SerializerMethodField()
    time_until_start = serializers.SerializerMethodField()

    class Meta:
        model = LiveSession
        fields = [
            'id', 'title', 'description', 'host_username', 'host_display_name',
            'starts_at', 'ends_at', 'duration_minutes', 'status',
            'participant_count', 'max_participants',
            'stream_url', 'recording_url', 'tags',
            'is_registered', 'time_until_start', 'created_at',
        ]

    def get_is_registered(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.registrations.filter(user=request.user).exists()

    def get_time_until_start(self, obj):
        from django.utils import timezone
        delta = obj.starts_at - timezone.now()
        return int(delta.total_seconds()) if delta.total_seconds() > 0 else 0
