import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class DiscussionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time discussion messages.
    
    URL: ws://.../ws/discussions/<thread_id>/
    """
    
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'discussion_{self.thread_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if thread exists and is accessible
        thread_exists = await self.check_thread_exists()
        if not thread_exists:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'thread_id': self.thread_id,
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'send_message':
                await self.handle_send_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON')
        except Exception as e:
            await self.send_error(str(e))
    
    async def handle_send_message(self, data):
        """Handle new message from user."""
        content = data.get('content', '').strip()
        
        if not content:
            await self.send_error('Message cannot be empty')
            return
        
        # Check if thread is locked
        is_locked = await self.is_thread_locked()
        if is_locked:
            await self.send_error('Thread is locked')
            return
        
        # Save message to database
        message = await self.save_message(content)
        
        if not message:
            await self.send_error('Failed to save message')
            return
        
        # Broadcast message to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message['id'],
                    'author_name': message['author_name'],
                    'author_email': message['author_email'],
                    'content': message['content'],
                    'created_at': message['created_at'],
                    'is_author': False,  # Will be set per-client
                }
            }
        )
    
    async def handle_typing(self, data):
        """Handle typing indicator."""
        is_typing = data.get('is_typing', False)
        
        # Broadcast typing status to room (except sender)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'user_email': self.user.email,
                'user_name': self.user.full_name,
                'is_typing': is_typing,
            }
        )
    
    async def chat_message(self, event):
        """Send message to WebSocket."""
        message = event['message']
        
        # Mark if current user is the author
        message['is_author'] = (message['author_email'] == self.user.email)
        
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message,
        }))
    
    async def user_typing(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send to the user who is typing
        if event['user_email'] != self.user.email:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_email': event['user_email'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
            }))
    
    async def send_error(self, error_message):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error': error_message,
        }))
    
    @database_sync_to_async
    def check_thread_exists(self):
        """Check if thread exists."""
        from .models import DiscussionThread
        return DiscussionThread.objects.filter(id=self.thread_id).exists()
    
    @database_sync_to_async
    def is_thread_locked(self):
        """Check if thread is locked."""
        from .models import DiscussionThread
        try:
            thread = DiscussionThread.objects.get(id=self.thread_id)
            return thread.is_locked
        except DiscussionThread.DoesNotExist:
            return True
    
    @database_sync_to_async
    def save_message(self, content):
        """Save message to database."""
        from .models import DiscussionThread, DiscussionMessage
        
        try:
            thread = DiscussionThread.objects.get(id=self.thread_id)
            
            if thread.is_locked:
                return None
            
            message = DiscussionMessage.objects.create(
                thread=thread,
                author=self.user,
                content=content,
            )
            
            return {
                'id': message.id,
                'author_name': message.author.full_name,
                'author_email': message.author.email,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
            }
        except DiscussionThread.DoesNotExist:
            return None