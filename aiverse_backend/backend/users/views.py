from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
from urllib import parse, request
import json
import uuid
from django.db import DatabaseError, IntegrityError

from .serializers import (
    UserPublicSerializer, UserProfileSerializer,
    RegisterSerializer, LoginSerializer,
    PortfolioProfileSerializer, PortfolioProjectSerializer,
)
from .models import Project
from utils.cache import (
    cache_bust,
    cache_get,
    cache_set,
    profile_cache_key,
    CacheTTL,
)
from ml.models import Submission

User = get_user_model()


def _google_json_request(url, payload=None):
    """Perform a small JSON HTTP request against Google OAuth endpoints."""
    if payload is None:
        req = request.Request(url, method='GET')
    else:
        encoded = parse.urlencode(payload).encode('utf-8')
        req = request.Request(url, data=encoded, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))


def _unique_username_from_email(email):
    """Generate a unique username from email local-part."""
    base = (email.split('@')[0] or 'user').strip().lower().replace(' ', '')
    candidate = base[:45] or f"user_{uuid.uuid4().hex[:6]}"
    index = 1
    while User.objects.filter(username=candidate).exists():
        suffix = f"_{index}"
        candidate = f"{base[:max(1, 50 - len(suffix))]}{suffix}"
        index += 1
    return candidate


def _fetch_github_user(access_token):
    """Fetch GitHub user info using access token."""
    try:
        req = request.Request('https://api.github.com/user', method='GET')
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('Accept', 'application/vnd.github.v3+json')
        with request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return {
                'username': data.get('login', ''),
                'url': data.get('html_url', ''),
            }
    except Exception as e:
        raise ValueError(f'Failed to fetch GitHub user: {str(e)}')


def _fetch_linkedin_user(access_token):
    """Fetch LinkedIn user info using access token."""
    try:
        req = request.Request('https://api.linkedin.com/v2/me', method='GET')
        req.add_header('Authorization', f'Bearer {access_token}')
        with request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            user_id = data.get('id', '')
        
        profile_url = f'https://www.linkedin.com/in/{user_id}/'
        return {
            'id': user_id,
            'url': profile_url,
        }
    except Exception as e:
        raise ValueError(f'Failed to fetch LinkedIn user: {str(e)}')


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        """Authenticate user via Google id_token/code and return JWT tokens."""
        id_token = request.data.get('id_token') or request.data.get('credential')
        auth_code = request.data.get('code')

        if auth_code and not id_token:
            if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_CLIENT_SECRET:
                return Response(
                    {'error': 'Google OAuth client credentials are not configured'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            try:
                token_data = _google_json_request(
                    settings.GOOGLE_TOKEN_ENDPOINT,
                    payload={
                        'code': auth_code,
                        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
                        'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
                        'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
                        'grant_type': 'authorization_code',
                    },
                )
                id_token = token_data.get('id_token')
            except Exception:
                return Response(
                    {'error': 'Failed to exchange Google authorization code'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not id_token:
            return Response(
                {'error': 'Missing Google credential (id_token/credential/code)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tokeninfo_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={parse.quote(id_token)}"
            tokeninfo = _google_json_request(tokeninfo_url)
        except Exception:
            return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)

        expected_client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', None)
        token_aud = (tokeninfo.get('aud') or '').strip()
        if expected_client_id and token_aud and token_aud != expected_client_id:
            return Response(
                {'error': 'Google token audience mismatch for configured client ID'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = (tokeninfo.get('email') or '').strip().lower()
        email_verified = str(tokeninfo.get('email_verified', '')).lower() == 'true'

        if not email:
            return Response({'error': 'Google account email not available'}, status=status.HTTP_400_BAD_REQUEST)
        if not email_verified:
            return Response({'error': 'Google email is not verified'}, status=status.HTTP_400_BAD_REQUEST)

        name = (tokeninfo.get('name') or '').strip()[:100]
        picture = (tokeninfo.get('picture') or '').strip()[:200]

        try:
            user = User.objects.filter(email__iexact=email).first()
            if user is None:
                user = User.objects.create(
                    email=email,
                    username=_unique_username_from_email(email),
                    display_name=name or email.split('@')[0],
                    avatar_url=picture,
                    auth_method='google',
                    is_active=True,
                )
                user.set_unusable_password()
                user.save(update_fields=['password'])
            else:
                updated_fields = []
                if user.auth_method != 'google':
                    user.auth_method = 'google'
                    updated_fields.append('auth_method')
                if name and user.display_name != name:
                    user.display_name = name
                    updated_fields.append('display_name')
                if picture and user.avatar_url != picture:
                    user.avatar_url = picture
                    updated_fields.append('avatar_url')
                if updated_fields:
                    user.save(update_fields=updated_fields)
        except (IntegrityError, DatabaseError):
            return Response(
                {'error': 'Unable to create/update user from Google profile data'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserProfileSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, username=email, password=password)
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data,
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Successfully logged out.'})
        except (TokenError, Exception) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'profile'

    def get(self, request):
        cache_key = profile_cache_key(request.user.pk)
        cached = cache_get(cache_key)
        if cached:
            return Response(cached)
        data = UserProfileSerializer(request.user).data
        cache_set(cache_key, data, ttl=CacheTTL.PROFILE)
        return Response(data)

    def patch(self, request):
        EDITABLE = ['username', 'display_name', 'avatar_url', 'bio',
                    'github_url', 'linkedin_url', 'website_url', 'preferences']
        filtered = {k: v for k, v in request.data.items() if k in EDITABLE}
        serializer = UserProfileSerializer(
            request.user, data=filtered, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            cache_bust(profile_cache_key(request.user.pk))
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        return Response(UserPublicSerializer(user).data)


class PublicProfileByUsernameView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        return Response(UserPublicSerializer(user).data)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'profile'

    def get(self, request):
        user = request.user
        serialized = PortfolioProfileSerializer(user).data

        recent_submissions = list(
            Submission.objects.filter(user=user)
            .select_related('problem')
            .order_by('-created_at')[:2]
            .values('id', 'status', 'score', 'created_at', 'problem__title')
        )

        for row in recent_submissions:
            row['problem_title'] = row.pop('problem__title', 'Untitled Problem')

        serialized['activity_snapshot'] = {
            'last_active': user.last_active,
            'recent_submissions': recent_submissions,
            'current_streak': user.streak_days,
        }
        return Response(serialized)


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'profile'

    @transaction.atomic
    def put(self, request):
        user = request.user
        payload = request.data if isinstance(request.data, dict) else {}

        editable_fields = [
            'display_name', 'tagline', 'avatar_url', 'bio',
            'portfolio_url', 'website_url',
        ]

        for field in editable_fields:
            if field in payload:
                setattr(user, field, payload.get(field) or '')

        if 'skills' in payload:
            skills = payload.get('skills') or []
            if not isinstance(skills, list):
                return Response({'skills': 'Skills must be a list.'}, status=status.HTTP_400_BAD_REQUEST)
            cleaned_skills = [str(item).strip() for item in skills if str(item).strip()]
            user.skills = cleaned_skills[:12]

        user.save()

        if 'projects' in payload:
            projects = payload.get('projects') or []
            if not isinstance(projects, list):
                return Response({'projects': 'Projects must be a list.'}, status=status.HTTP_400_BAD_REQUEST)

            Project.objects.filter(user=user).delete()
            project_serializers = []
            for index, project in enumerate(projects[:4]):
                if not isinstance(project, dict):
                    continue
                project_payload = {
                    'title': str(project.get('title', '')).strip(),
                    'description': str(project.get('description', '')).strip(),
                    'tech_stack': project.get('tech_stack') if isinstance(project.get('tech_stack'), list) else [],
                    'github_url': str(project.get('github_url', '')).strip(),
                    'display_order': index,
                }
                project_serializer = PortfolioProjectSerializer(data=project_payload)
                if not project_serializer.is_valid():
                    return Response(project_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                project_serializers.append(project_serializer)

            for serializer in project_serializers:
                serializer.save(user=user)

        refreshed = PortfolioProfileSerializer(user).data
        recent_submissions = list(
            Submission.objects.filter(user=user)
            .select_related('problem')
            .order_by('-created_at')[:2]
            .values('id', 'status', 'score', 'created_at', 'problem__title')
        )
        for row in recent_submissions:
            row['problem_title'] = row.pop('problem__title', 'Untitled Problem')

        refreshed['activity_snapshot'] = {
            'last_active': user.last_active,
            'recent_submissions': recent_submissions,
            'current_streak': user.streak_days,
        }
        cache_bust(profile_cache_key(user.pk))
        return Response(refreshed)


class GitHubConnectView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'profile'

    def post(self, request):
        access_token = request.data.get('access_token', '')
        if not access_token:
            return Response({'error': 'Missing GitHub access token'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            github_info = _fetch_github_user(access_token)
            user = request.user
            user.github_username = github_info['username']
            user.github_url = github_info['url']
            user.github_token = access_token
            user.save(update_fields=['github_username', 'github_url', 'github_token'])
            
            cache_bust(profile_cache_key(user.pk))
            return Response({
                'github_connected': True,
                'github_url': user.github_url,
                'github_username': user.github_username,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GitHubDisconnectView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'profile'

    def post(self, request):
        user = request.user
        user.github_username = ''
        user.github_url = ''
        user.github_token = ''
        user.save(update_fields=['github_username', 'github_url', 'github_token'])
        cache_bust(profile_cache_key(user.pk))
        return Response({'github_connected': False})


class LinkedInConnectView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'profile'

    def post(self, request):
        access_token = request.data.get('access_token', '')
        if not access_token:
            return Response({'error': 'Missing LinkedIn access token'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            linkedin_info = _fetch_linkedin_user(access_token)
            user = request.user
            user.linkedin_id = linkedin_info['id']
            user.linkedin_url = linkedin_info['url']
            user.linkedin_token = access_token
            user.save(update_fields=['linkedin_id', 'linkedin_url', 'linkedin_token'])
            
            cache_bust(profile_cache_key(user.pk))
            return Response({
                'linkedin_connected': True,
                'linkedin_url': user.linkedin_url,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LinkedInDisconnectView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'profile'

    def post(self, request):
        user = request.user
        user.linkedin_id = ''
        user.linkedin_url = ''
        user.linkedin_token = ''
        user.save(update_fields=['linkedin_id', 'linkedin_url', 'linkedin_token'])
        cache_bust(profile_cache_key(user.pk))
        return Response({'linkedin_connected': False})
