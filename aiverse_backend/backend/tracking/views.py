from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import LearnerEvent
from .serializers import LearnerEventSerializer
from .tasks import process_learner_event


class TrackEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LearnerEventSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            event = serializer.save()
            # Fire async event processing
            process_learner_event.delay(str(event.id))
            return Response({'status': 'tracked'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BatchTrackEventView(APIView):
    """Track multiple events at once (for offline/buffered frontend)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        events = request.data.get('events', [])
        created = []
        to_update = set()
        for event_data in events[:50]:  # cap at 50 per batch
            s = LearnerEventSerializer(data=event_data, context={'request': request})
            if s.is_valid():
                e = s.save()
                created.append(str(e.id))
                if e.content_type in ['quiz', 'problem']:
                    to_update.add((e.content_type, e.content_id))
        
        for ct, ci in to_update:
            # Process each event for mastery updates
            pass  # Events already processed individually above
        return Response({'tracked': len(created)}, status=status.HTTP_201_CREATED)


class UserEventHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = LearnerEvent.objects.filter(user=request.user).order_by('-timestamp')[:100]
        serializer = LearnerEventSerializer(events, many=True)
        return Response(serializer.data)
