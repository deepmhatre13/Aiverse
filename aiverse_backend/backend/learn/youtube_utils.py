"""
YouTube URL parsing and validation utilities.

Extracts YouTube video IDs from various URL formats.
Validates and normalizes YouTube video identifiers.
"""

import re
from typing import Optional


def extract_youtube_id(url_or_id: str) -> Optional[str]:
    """
    Extract YouTube video ID from URL or return ID if already extracted.
    
    Supports formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://youtube.com/watch?v=VIDEO_ID&feature=share
    - VIDEO_ID (raw ID)
    
    Args:
        url_or_id: YouTube URL or video ID
        
    Returns:
        Video ID string or None if invalid
    """
    if not url_or_id or not isinstance(url_or_id, str):
        return None
    
    url_or_id = url_or_id.strip()
    
    # If it's already just an ID (alphanumeric, dashes, underscores, 11 chars typical)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    
    # Pattern for youtube.com/watch?v=
    match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})', url_or_id)
    if match:
        return match.group(1)
    
    # Try to extract any 11-character alphanumeric sequence (fallback)
    match = re.search(r'([a-zA-Z0-9_-]{11})', url_or_id)
    if match:
        return match.group(1)
    
    return None


def is_valid_youtube_id(video_id: str) -> bool:
    """
    Validate YouTube video ID format.
    
    YouTube IDs are typically 11 characters (alphanumeric, dashes, underscores).
    
    Args:
        video_id: Video ID to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not video_id or not isinstance(video_id, str):
        return False
    
    video_id = video_id.strip()
    
    # YouTube IDs are typically 11 characters
    # Allow 10-12 for flexibility
    if not re.match(r'^[a-zA-Z0-9_-]{10,12}$', video_id):
        return False
    
    return True


def normalize_youtube_input(input_value: str) -> Optional[str]:
    """
    Normalize YouTube input (URL or ID) to just the video ID.
    
    This is the main function to use when processing user input.
    
    Args:
        input_value: YouTube URL or video ID from user
        
    Returns:
        Normalized video ID or None if invalid
    """
    if not input_value:
        return None
    
    video_id = extract_youtube_id(input_value)
    
    if video_id and is_valid_youtube_id(video_id):
        return video_id
    
    return None
