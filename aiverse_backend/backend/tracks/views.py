from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Track
from .serializers import TrackSerializer


class TrackViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Track endpoints.
    Allows public read-only access to active tracks.
    """
    serializer_class = TrackSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Get only active tracks"""
        return Track.objects.filter(is_active=True).order_by('name')

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def active(self, request):
        """Get all active tracks"""
        tracks = Track.objects.filter(is_active=True).order_by('name')
        serializer = self.get_serializer(tracks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def courses(self, request, slug=None):
        """Get all courses in a track"""
        track = self.get_object()
        # TODO: Implement course filtering by track
        return Response({'message': f'Courses for track: {track.name}'})

