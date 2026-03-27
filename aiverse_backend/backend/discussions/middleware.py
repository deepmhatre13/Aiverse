"""
Custom middleware for Channels authentication.
"""
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_string):
    """Get user from JWT token."""
    try:
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
        return user
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware:
    """
    Custom middleware to authenticate WebSocket connections via JWT.
    
    Extracts token from query string: ws://.../?token=<jwt_token>
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        try:
            # Extract token from query string (?token=...)
            query_string = scope.get('query_string', b'').decode()
            query_params = {}
            for qc in query_string.split('&'):
                if '=' in qc:
                    k, v = qc.split('=', 1)  # Split only on first =
                    query_params[k] = v
            token = query_params.get('token')
            
            if token:
                scope['user'] = await get_user_from_token(token)
            else:
                scope['user'] = AnonymousUser()
        except Exception:
            scope['user'] = AnonymousUser()
        
        return await self.app(scope, receive, send)