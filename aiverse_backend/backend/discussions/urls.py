from django.urls import path
from .views import (
    CategoryListView,
    ThreadListView,
    ThreadCreateView,
    ThreadDetailView,
    PostListView,
    PostCreateView,
    toggle_post_like,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view()),
    path("threads/", ThreadListView.as_view()),
    path("threads/create/", ThreadCreateView.as_view()),
    path("threads/<int:pk>/", ThreadDetailView.as_view()),

    # 🔥 THIS IS THE FIX
    path(
        "threads/<int:thread_id>/messages/",
        PostListView.as_view(),
        name="thread-messages",
    ),
    path(
        "threads/<int:thread_id>/messages/create/",
        PostCreateView.as_view(),
        name="thread-message-create",
    ),
    path(
        "posts/<int:post_id>/like/",
        toggle_post_like,
        name="post-like",
    ),
]
