from django.urls import path
from . import views

app_name = 'mentor'

urlpatterns = [
    # FRONTEND EXPECTED ROUTES (use <int:session_id> for integer ID path conversion)
    path('session/start/', views.start_session, name='start-session'),  # POST: create new session
    path('sessions/', views.get_sessions, name='list-sessions'),  # GET: list sessions
    path('session/<int:session_id>/messages/', views.MentorMessageListCreateView.as_view(), name='mentor-message-list-create'),  # GET/POST: messages
    path('session/<int:session_id>/ask/', views.ask_mentor_v2, name='ask-mentor-v2'),  # POST: ask question (singular)
    
    # BACKWARD COMPATIBILITY (plural routes, kept for internal use)
    path('sessions/<int:session_id>/', views.get_session_detail, name='session-detail'),  # GET: fetch single session
    path('sessions/<int:session_id>/messages/', views.get_messages, name='get-messages'),  # GET: fetch messages
    path('sessions/<int:session_id>/ask/', views.ask_mentor, name='ask-mentor'),  # POST: ask question (plural)
    
    # Task status (Async tracking)
    path('task/<str:task_id>/status/', views.check_task_status, name='task-status'),  # GET: check task status
    
    # Diagnostic endpoint (no auth required)
    path('test-gemini/', views.test_gemini, name='test-gemini'),  # GET: test Gemini connectivity
]
