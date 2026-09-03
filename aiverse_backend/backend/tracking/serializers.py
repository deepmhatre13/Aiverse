from rest_framework import serializers
from .models import LearnerEvent


class LearnerEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnerEvent
        fields = ['event_type', 'content_type', 'content_id', 'metadata', 'session_id']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        ip = self.context['request'].META.get('REMOTE_ADDR')
        validated_data['ip_address'] = ip
        return super().create(validated_data)
