from rest_framework import permissions


class IsSessionOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a session to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Session owner check
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # MentorMessage owner check via session
        if hasattr(obj, 'session'):
            return obj.session.user == request.user
        return False