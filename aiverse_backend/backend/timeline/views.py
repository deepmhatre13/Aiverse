from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from .models import ActivityEvent, PerformanceSnapshot
from .serializers import ActivityEventSerializer, PerformanceSnapshotSerializer


class ActivityEventListView(generics.ListAPIView):
    """
    Get user's activity timeline
    Supports filtering by date range and event type
    """
    serializer_class = ActivityEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ActivityEvent.objects.filter(user=self.request.user)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        return queryset.select_related('user')


class PerformanceSnapshotListView(generics.ListAPIView):
    """
    Get user's performance snapshots over time
    Supports filtering and grouping
    """
    serializer_class = PerformanceSnapshotSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = PerformanceSnapshot.objects.filter(user=self.request.user)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.select_related('user')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def timeline_summary(request):
    """
    Get a summary of user's timeline activity
    """
    user = request.user
    
    # Get date range (default to last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    start_param = request.query_params.get('start_date')
    end_param = request.query_params.get('end_date')
    
    if start_param:
        from datetime import datetime
        start_date = datetime.strptime(start_param, '%Y-%m-%d').date()
    if end_param:
        from datetime import datetime
        end_date = datetime.strptime(end_param, '%Y-%m-%d').date()
    
    # Activity counts by type
    from django.db.models import Count
    activity_counts = ActivityEvent.objects.filter(
        user=user,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).values('event_type').annotate(count=Count('id'))
    
    # Performance summary
    snapshots = PerformanceSnapshot.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    )
    
    total_problems_attempted = sum(s.problems_attempted for s in snapshots)
    total_problems_solved = sum(s.problems_solved for s in snapshots)
    
    if total_problems_attempted > 0:
        overall_success_rate = (total_problems_solved / total_problems_attempted) * 100
    else:
        overall_success_rate = 0.0
    
    # Active days
    active_days = snapshots.filter(problems_attempted__gt=0).count()
    
    # Recent activity (last 7 days)
    recent_events = ActivityEvent.objects.filter(
        user=user,
        created_at__date__gte=end_date - timedelta(days=7)
    ).order_by('-created_at')[:10]
    
    recent_serializer = ActivityEventSerializer(recent_events, many=True)
    
    return Response({
        'date_range': {
            'start': start_date,
            'end': end_date
        },
        'activity_counts': {item['event_type']: item['count'] for item in activity_counts},
        'performance_summary': {
            'total_problems_attempted': total_problems_attempted,
            'total_problems_solved': total_problems_solved,
            'overall_success_rate': round(overall_success_rate, 2),
            'active_days': active_days
        },
        'recent_activity': recent_serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_snapshot(request):
    """
    Manually trigger snapshot generation for today
    """
    today = timezone.now().date()
    snapshot = PerformanceSnapshot.generate_for_date(request.user, today)
    serializer = PerformanceSnapshotSerializer(snapshot)
    
    return Response({
        'message': 'Snapshot generated',
        'snapshot': serializer.data
    })