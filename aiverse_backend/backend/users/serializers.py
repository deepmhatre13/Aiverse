from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Project

User = get_user_model()


class UserPublicSerializer(serializers.ModelSerializer):
    """Safe fields for public profile view (/u/username)."""
    success_rate = serializers.FloatField(read_only=True)
    github_connected = serializers.SerializerMethodField()
    linkedin_connected = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'display_name', 'tagline', 'avatar_url', 'bio',
            'github_url', 'github_connected', 'linkedin_url', 'linkedin_connected',
            'website_url', 'portfolio_url', 'skills',
            'total_score', 'global_rank', 'problems_solved',
            'courses_completed', 'streak_days', 'longest_streak',
            'badges', 'joined_at', 'is_pro',
        ]
        read_only_fields = fields

    def get_github_connected(self, obj):
        return bool(obj.github_username and obj.github_token)

    def get_linkedin_connected(self, obj):
        return bool(obj.linkedin_id and obj.linkedin_token)


class UserProfileSerializer(serializers.ModelSerializer):
    """Full profile for /api/profile/me/ — includes private stats."""
    success_rate = serializers.FloatField(read_only=True)
    display = serializers.CharField(read_only=True)
    github_connected = serializers.SerializerMethodField()
    linkedin_connected = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'display_name', 'display',
            'tagline', 'avatar_url', 'bio', 'github_url', 'github_connected',
            'linkedin_url', 'linkedin_connected', 'website_url', 'portfolio_url', 'skills',
            'joined_at', 'last_active',
            'total_score', 'global_rank', 'weekly_score', 'monthly_score',
            'problems_solved', 'courses_completed',
            'total_submissions', 'accepted_submissions', 'success_rate',
            'streak_days', 'longest_streak', 'last_submission_date',
            'is_pro', 'badges', 'preferences',
        ]
        read_only_fields = [
            'id', 'email', 'joined_at', 'last_active',
            'total_score', 'global_rank', 'weekly_score', 'monthly_score',
            'problems_solved', 'courses_completed',
            'total_submissions', 'accepted_submissions', 'success_rate',
            'streak_days', 'longest_streak', 'last_submission_date',
            'is_pro', 'badges', 'display', 'github_connected', 'linkedin_connected',
        ]

    def get_github_connected(self, obj):
        return bool(obj.github_username and obj.github_token)

    def get_linkedin_connected(self, obj):
        return bool(obj.linkedin_id and obj.linkedin_token)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    tokens = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'tokens']

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PortfolioProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'tech_stack', 'github_url', 'display_order']
        read_only_fields = ['id']


class PortfolioProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    projects = PortfolioProjectSerializer(many=True, read_only=True)
    github_connected = serializers.SerializerMethodField()
    linkedin_connected = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'display_name', 'username', 'email', 'tagline', 'avatar_url',
            'bio', 'github_url', 'github_connected', 'linkedin_url', 'linkedin_connected',
            'portfolio_url', 'skills', 'joined_at', 'last_active', 'streak_days', 'projects',
        ]

    def get_full_name(self, obj):
        return obj.display_name or obj.get_full_name() or obj.username or obj.email

    def get_github_connected(self, obj):
        return bool(obj.github_username and obj.github_token)

    def get_linkedin_connected(self, obj):
        return bool(obj.linkedin_id and obj.linkedin_token)