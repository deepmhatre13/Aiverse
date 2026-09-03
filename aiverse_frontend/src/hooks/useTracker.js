import { useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { trackEvent, Events } from '../api/trackingApi';

export function useTracker() {
  const { isAuthenticated } = useAuth();

  const track = useCallback(
    (eventType, contentType, contentId, metadata = {}) => {
      if (!isAuthenticated) return;
      trackEvent(eventType, contentType, contentId, metadata);
    },
    [isAuthenticated]
  );

  return { track, Events };
}
