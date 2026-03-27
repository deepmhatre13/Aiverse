/**
 * Social Links Component - Usage Examples & Patterns
 * 
 * This file demonstrates various use cases and integration patterns
 */

import { useState } from 'react';
import SocialLinks from './SocialLinks';

/**
 * ✅ BASIC USAGE - Minimal with full data
 */
export function BasicUsageExample() {
  const profile = {
    github_url: 'https://github.com/deepmhatre13',
    linkedin_url: 'https://linkedin.com/in/deepam-mhatre',
    portfolio_url: 'https://example.com',
  };

  return <SocialLinks profile={profile} />;
}

/**
 * ✅ WITH PARTIAL DATA - Some links empty
 */
export function PartialDataExample() {
  const profile = {
    github_url: 'https://github.com/deepmhatre13',
    linkedin_url: null, // Not set yet
    portfolio_url: 'https://example.com',
  };

  return <SocialLinks profile={profile} />;
}

/**
 * ✅ WITH EMPTY DATA - No links connected
 */
export function EmptyStateExample() {
  const profile = {
    github_url: null,
    linkedin_url: null,
    portfolio_url: null,
  };

  return <SocialLinks profile={profile} />;
}

/**
 * ✅ WITH PROFILE UPDATE CALLBACK
 * Shows how to handle profile updates in parent component
 */
export function WithUpdateCallbackExample() {
  const [profile, setProfile] = useState({
    github_url: 'https://github.com/deepmhatre13',
    linkedin_url: null,
    portfolio_url: null,
  });

  const [saveStatus, setSaveStatus] = useState(null);

  const handleProfileUpdate = (updatedProfile) => {
    setProfile(updatedProfile);
    setSaveStatus('Profile updated successfully!');
    
    // Clear message after 3 seconds
    setTimeout(() => setSaveStatus(null), 3000);
  };

  return (
    <div className="space-y-4">
      {saveStatus && (
        <div className="p-3 bg-green-900/20 border border-green-900/50 rounded-lg text-green-200">
          {saveStatus}
        </div>
      )}
      <SocialLinks profile={profile} onProfileUpdate={handleProfileUpdate} />
    </div>
  );
}

/**
 * ✅ INTEGRATED IN PROFILE PAGE
 * Full example showing how to fetch and display profile
 */
export function IntegratedProfilePageExample() {
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch profile on mount
  React.useEffect(() => {
    const fetchProfile = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('/api/users/profile/');
        if (!response.ok) throw new Error('Failed to fetch profile');
        const data = await response.json();
        setProfile(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, []);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* Profile Header */}
      <div>
        <h1 className="text-3xl font-bold">{profile?.full_name}</h1>
        <p className="text-gray-400">{profile?.tagline}</p>
      </div>

      {/* Social Links */}
      <SocialLinks profile={profile} onProfileUpdate={setProfile} />

      {/* Other sections */}
    </div>
  );
}

/**
 * ✅ WITH TOAST NOTIFICATIONS
 * Shows how to add toast feedback using your toast library
 */
export function WithToastNotificationsExample() {
  const [profile, setProfile] = useState({
    github_url: 'https://github.com/deepmhatre13',
    linkedin_url: null,
    portfolio_url: null,
  });

  // Assuming you have a toast hook
  const { toast } = useToast?.(); // from your UI library

  const handleProfileUpdate = (updatedProfile) => {
    setProfile(updatedProfile);
    
    // Show success toast
    if (toast) {
      toast({
        title: 'Success',
        description: 'Profile updated!',
        variant: 'default',
      });
    }
  };

  return <SocialLinks profile={profile} onProfileUpdate={handleProfileUpdate} />;
}

/**
 * ✅ DIFFERENT PROFILE DATA STRUCTURES
 * Shows how to handle different API response formats
 */
export function DifferentDataStructuresExample() {
  // Format 1: Direct URL fields
  const format1 = {
    github_url: 'https://github.com/user',
    linkedin_url: 'https://linkedin.com/in/user',
    portfolio_url: 'https://user.com',
  };

  // Format 2: Nested social object
  const format2 = {
    social: {
      github_url: 'https://github.com/user',
      linkedin_url: 'https://linkedin.com/in/user',
      portfolio_url: 'https://user.com',
    },
  };

  // Convert format 2 to format 1 for component
  const normalizedFormat2 = format2.social;

  return <SocialLinks profile={normalizedFormat2} />;
}

/**
 * ✅ EDITABLE PROFILE CONTEXT
 * Shows how to use with React Context for global profile state
 */
import { createContext, useContext } from 'react';

const ProfileContext = createContext();

export function ProfileProvider({ children }) {
  const [profile, setProfile] = useState(null);

  const updateProfile = (updatedProfile) => {
    setProfile(updatedProfile);
  };

  return (
    <ProfileContext.Provider value={{ profile, updateProfile }}>
      {children}
    </ProfileContext.Provider>
  );
}

export function WithContextExample() {
  const { profile, updateProfile } = useContext(ProfileContext);

  return <SocialLinks profile={profile} onProfileUpdate={updateProfile} />;
}

/**
 * ✅ ERROR BOUNDARY WRAPPER
 * Shows how to handle component errors gracefully
 */
export function WithErrorBoundaryExample() {
  return (
    <ErrorBoundary fallback={<div>Failed to load social links</div>}>
      <SocialLinks profile={{}} />
    </ErrorBoundary>
  );
}

/**
 * ✅ LOADING STATE
 * Shows how to display skeleton while fetching
 */
export function WithLoadingSkeletonExample() {
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  React.useEffect(() => {
    // Simulate API delay
    setTimeout(() => {
      setProfile({
        github_url: 'https://github.com/deepmhatre13',
        linkedin_url: null,
        portfolio_url: null,
      });
      setIsLoading(false);
    }, 1000);
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-6 bg-gray-700 rounded animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-gray-700 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return <SocialLinks profile={profile} />;
}

/**
 * KEYBOARD SHORTCUTS
 * Reference for keyboard interactions available in modal
 * 
 * Enter → Save URL
 * Esc   → Close modal without saving
 * Tab   → Navigate between inputs and buttons
 */

/**
 * URL FORMATS SUPPORTED
 * 
 * GitHub:
 *   https://github.com/username
 *   github.com/username (auto-prefixed)
 *   
 * LinkedIn:
 *   https://linkedin.com/in/profile-name
 *   https://www.linkedin.com/in/profile-name
 *   linkedin.com/in/profile-name (auto-prefixed)
 *   
 * Portfolio:
 *   https://yoursite.com
 *   Any valid HTTPS URL
 */

/**
 * CUSTOMIZATION POINTS
 * 
 * 1. Colors: Update SOCIAL_CONFIG in SocialLinks.jsx
 * 2. Labels: Modify placeholder text in SOCIAL_CONFIG
 * 3. Validation: Add rules in urlUtils.js validateSocialUrl()
 * 4. Icons: Replace Lucide icons with your own
 * 5. Animations: Modify Framer Motion in SocialCard
 * 6. Styling: Adjust Tailwind classes throughout
 */

/**
 * ACCESSIBILITY FEATURES
 * 
 * ✅ Semantic HTML (button, dialog, input)
 * ✅ ARIA labels and descriptions
 * ✅ Keyboard navigation (Tab, Enter, Esc)
 * ✅ Focus management in modal
 * ✅ Error announcements
 * ✅ Loading state indicators
 */

/**
 * PERFORMANCE CONSIDERATIONS
 * 
 * ✅ useCallback for memoized handlers
 * ✅ Lazy modal rendering
 * ✅ Minimal re-renders with proper state
 * ✅ Optimistic UI updates
 * ✅ Efficient API calls (single field update)
 */
