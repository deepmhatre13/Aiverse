"""
WebSocket consumer for Live Performance Center real-time updates.

URL: ws://.../ws/live-updates/<user_id>/

Broadcasts:
- submission_created: When user submits code
- evaluation_started: When evaluation begins
- evaluation_completed: When evaluation finishes
- rank_changed: When user's rank changes
- score_updated: When best score improves
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class LiveUpdatesConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time performance updates.
    
    Each user has their own channel group: live_updates_{user_id}
    Server broadcasts updates to the user's group when events occur.
    
    Defensive: Catches exceptions in connect(), never crashes consumer.
    """
    
    async def connect(self):
        try:
            self.user = self.scope.get("user")
            
            if not self.user or not getattr(self.user, "is_authenticated", False):
                await self.close(code=4001)
                return
            
            url_user_id = self.scope.get("url_route", {}).get("kwargs", {}).get("user_id")
            if url_user_id and str(getattr(self.user, "id", None)) != str(url_user_id):
                await self.close(code=4003)
                return
            
            self.user_id = self.user.id
            self.room_group_name = f"live_updates_{self.user_id}"
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            initial_data = await self.get_initial_data()
            await self.send(text_data=json.dumps({
                "type": "connection_established",
                "user_id": self.user_id,
                "data": initial_data,
                "server_time": timezone.now().isoformat(),
            }))
        except Exception as exc:
            logger.exception("LiveUpdatesConsumer connect failed: %s", exc)
            try:
                await self.close(code=1011)
            except Exception:
                pass
    
    async def disconnect(self, close_code):
        # Leave user's group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming messages from client (ping/pong, subscription changes)."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'server_time': timezone.now().isoformat(),
                }))
            
            elif message_type == 'request_refresh':
                # Client requests fresh data
                fresh_data = await self.get_initial_data()
                await self.send(text_data=json.dumps({
                    'type': 'data_refresh',
                    'data': fresh_data,
                    'server_time': timezone.now().isoformat(),
                }))
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON',
            }))
    
    # ========== Event Handlers (called via channel_layer.group_send) ==========
    
    async def submission_created(self, event):
        """Broadcast when a new submission is created."""
        await self.send(text_data=json.dumps({
            'type': 'submission_created',
            'submission_id': event['submission_id'],
            'problem': event.get('problem'),
            'timestamp': event.get('timestamp'),
        }))
    
    async def evaluation_started(self, event):
        """Broadcast when evaluation begins."""
        await self.send(text_data=json.dumps({
            'type': 'evaluation_started',
            'submission_id': event['submission_id'],
            'timestamp': event.get('timestamp'),
        }))
    
    async def evaluation_completed(self, event):
        """Broadcast when evaluation completes."""
        await self.send(text_data=json.dumps({
            'type': 'evaluation_completed',
            'submission_id': event['submission_id'],
            'status': event.get('status'),
            'score': event.get('score'),
            'metric': event.get('metric'),
            'execution_time': event.get('execution_time'),
            'best_metric': event.get('best_metric'),
            'rank': event.get('rank'),
            'timestamp': event.get('timestamp'),
        }))
    
    async def rank_changed(self, event):
        """Broadcast when user's rank changes."""
        await self.send(text_data=json.dumps({
            'type': 'rank_changed',
            'old_rank': event.get('old_rank'),
            'new_rank': event.get('new_rank'),
            'problem': event.get('problem'),
            'timestamp': event.get('timestamp'),
        }))
    
    async def score_updated(self, event):
        """Broadcast when user achieves a new best score."""
        await self.send(text_data=json.dumps({
            'type': 'score_updated',
            'problem': event.get('problem'),
            'old_score': event.get('old_score'),
            'new_score': event.get('new_score'),
            'metric': event.get('metric'),
            'timestamp': event.get('timestamp'),
        }))
    
    async def streak_updated(self, event):
        """Broadcast when user's streak is updated."""
        await self.send(text_data=json.dumps({
            'type': 'streak_updated',
            'current_streak': event.get('current_streak'),
            'timestamp': event.get('timestamp'),
        }))
    
    # ========== Helper Methods ==========
    
    @database_sync_to_async
    def get_initial_data(self):
        """Get initial summary data for the user."""
        from ml.models import Submission
        from django.db.models import Max, Count, Q
        
        user_submissions = Submission.objects.filter(user=self.user)
        
        # Latest submission
        latest = user_submissions.order_by('-created_at').first()
        
        # Stats
        total = user_submissions.count()
        accepted = user_submissions.filter(status='ACCEPTED').count()
        
        # Best score
        best = user_submissions.filter(status='ACCEPTED').order_by('-score').first()
        
        # Calculate rank
        rank = None
        if best:
            user_best_score = best.score
            users_with_better = Submission.objects.filter(
                status='ACCEPTED'
            ).values('user').annotate(
                best_score=Max('score')
            ).filter(best_score__gt=user_best_score).count()
            rank = users_with_better + 1
        
        return {
            'summary': {
                'total_submissions': total,
                'accepted_count': accepted,
                'best_score': float(best.score) if best else None,
                'global_rank': rank,
                'latest_status': latest.status if latest else None,
            },
            'latest_submission': {
                'id': latest.id,
                'status': latest.status,
                'score': float(latest.score) if latest and latest.score else None,
                'problem_title': latest.problem.title if latest else None,
                'timestamp': latest.created_at.isoformat() if latest else None,
            } if latest else None,
        }


# ========== Utility Functions for Broadcasting ==========

def broadcast_submission_event(user_id, event_type, data):
    """
    Utility function to broadcast events to a user's WebSocket channel.
    
    Call this from Django views/tasks after submission events occur.
    
    Usage:
        from dashboard.consumers import broadcast_submission_event
        
        broadcast_submission_event(user.id, 'evaluation_completed', {
            'submission_id': submission.id,
            'status': 'ACCEPTED',
            'score': 0.95,
            ...
        })
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    room_group_name = f'live_updates_{user_id}'
    
    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {
            'type': event_type.replace('-', '_'),  # Convert to method name format
            **data,
        }
    )
