# Social & Presence Component Documentation

A polished, production-ready social media link component with URL parsing, validation, edit modal, and seamless API integration.

## 📦 Files Included

### 1. **SocialLinks.jsx** (Main Component)
The core profile section displaying GitHub, LinkedIn, and Portfolio links.

**Props:**
```js
{
  profile: {
    github_url?: string,
    linkedin_url?: string,
    portfolio_url?: string
  },
  onProfileUpdate?: (updatedProfile) => void
}
```

**Key Features:**
- ✅ Shows clean usernames (not full URLs)
- ✅ Clickable cards that open links in new tab
- ✅ Edit mode with validation
- ✅ Empty state with helpful placeholders
- ✅ Smooth animations and hover effects
- ✅ Error handling and loading states

---

### 2. **SocialEditModal.jsx** (Edit Modal)
Modal dialog for editing social URLs with validation.

**Props:**
```js
{
  isOpen: boolean,
  onClose: () => void,
  socialType: 'github' | 'linkedin' | 'portfolio',
  currentUrl?: string,
  onSave: (url: string | null) => void,
  isLoading?: boolean
}
```

**Features:**
- ✅ Easy-to-use input with platform hints
- ✅ Real-time validation with error messages
- ✅ Remove button to clear URL
- ✅ Keyboard shortcuts (Enter to save, Esc to close)
- ✅ Loading state with spinner

---

### 3. **urlUtils.js** (URL Parsing & Validation)
Utility functions for URL extraction, normalization, and validation.

**Functions:**

#### `normalizeUrl(value: string): string`
Ensures URL has protocol.
```js
normalizeUrl('github.com/user') // → 'https://github.com/user'
```

#### `getDisplayText(type: string, url: string): string`
Extracts display text based on platform.
```js
getDisplayText('github', 'https://github.com/deepmhatre13')
// → 'deepmhatre13'

getDisplayText('linkedin', 'https://linkedin.com/in/deepam-mhatre')
// → 'deepam-mhatre'

getDisplayText('portfolio', 'https://example.com')
// → 'Visit Website'
```

#### `validateSocialUrl(type: string, url: string): { valid: boolean, error?: string }`
Validates URL against platform requirements.
```js
validateSocialUrl('github', 'https://github.com/deepmhatre13')
// → { valid: true }

validateSocialUrl('linkedin', 'https://github.com/user')
// → { valid: false, error: 'Please enter a valid LinkedIn URL' }
```

#### `getPlaceholder(type: string): string`
Returns placeholder for input field.
```js
getPlaceholder('github')     // → 'https://github.com/username'
getPlaceholder('linkedin')   // → 'https://linkedin.com/in/your-name'
getPlaceholder('portfolio')  // → 'https://yourwebsite.com'
```

---

### 4. **profile.js** (API Service)
Backend API integration for fetching and updating profiles.

**Functions:**

#### `fetchProfile(): Promise<Profile>`
Fetches current user profile.

#### `updateProfileSocial(fieldName: string, url: string | null): Promise<Profile>`
Updates a single social URL.
```js
await updateProfileSocial('github_url', 'https://github.com/deepmhatre13');
```

#### `updateProfile(data: object): Promise<Profile>`
Updates entire profile.

---

## 🎨 UI States

### 1. **Connected State** (URL exists)
```
┌─────────────────────────┐
│ GITHUB                ✏  │
│ 🐙 deepmhatre13      ⤴  │
└─────────────────────────┘
```
- Shows clean username
- Edit icon on hover
- Entire card is clickable
- External link icon visible

### 2. **Empty State** (No URL)
```
┌─────────────────────────┐
│ GITHUB                  │
│ 🐙 Add GitHub profile   │
└─────────────────────────┘
```
- Placeholder text
- Click to edit
- No external link icon

### 3. **Edit Modal**
```
┌──────────────────────────────┐
│ GitHub Profile            ✕  │
│ Add your GitHub profile     │
├──────────────────────────────┤
│ Profile URL                  │
│ [https://github.com/...]     │
│                              │
│ ❌ Error message if invalid  │
├──────────────────────────────┤
│            Cancel    Save    │
└──────────────────────────────┘
```

---

## 💻 Usage Example

```jsx
import SocialLinks from '@/components/profile/SocialLinks';

export default function ProfilePage() {
  const [profile, setProfile] = useState(null);

  const handleProfileUpdate = (updatedProfile) => {
    setProfile(updatedProfile);
    // Show success toast, etc.
  };

  return (
    <div className="space-y-8">
      {/* Other profile sections */}
      
      <SocialLinks
        profile={profile}
        onProfileUpdate={handleProfileUpdate}
      />
    </div>
  );
}
```

---

## 🔒 Validation Rules

### GitHub
- ✅ Must be valid URL
- ✅ Must contain `github.com`
- ✅ Must have username after domain

### LinkedIn
- ✅ Must be valid URL
- ✅ Must contain `linkedin.com`
- ✅ Must have profile name

### Portfolio
- ✅ Must be valid URL
- ✅ No platform restrictions

---

## 🎯 Interaction Flow

```
User clicks card
    ↓
if connected → Opens URL in new tab
if empty → Opens edit modal
    ↓
User edits URL
    ↓
Validation runs
    ↓
if invalid → Shows error
if valid → Saves to API
    ↓
Updates component state
    ↓
Component re-renders
```

---

## 🚀 Features Highlights

### URL Extraction
- **No raw URLs** displayed to users
- **Clean, platform-specific text** (usernames, display names)
- **Smart parsing** for different URL formats

### Validation
- **Real-time error messages** during editing
- **Platform-specific checks** (GitHub URL must contain github.com)
- **User-friendly error copy**

### UX Polish
- **Smooth animations** (hover lift, click feedback)
- **Instant feedback** on interactions
- **Loading states** while saving
- **Error recovery** with helpful messages
- **Keyboard shortcuts** in modal (Enter, Esc)

### API Integration
- **Optimistic updates** for instant feedback
- **Error handling** with fallback messages
- **Loading states** during API calls
- **PATCH/PUT semantics** following REST best practices

---

## 📊 Component Architecture

```
SocialLinks (Main Container)
├── State
│   ├── editingType (which platform to edit)
│   ├── isSaving (loading state)
│   └── error (error message)
├── SocialCard (Repeatable per platform)
│   ├── Connected State
│   │   ├── Icon
│   │   ├── Username/Display text
│   │   ├── Edit button
│   │   └── External link button
│   └── Empty State
│       ├── Icon
│       └── Placeholder text
└── SocialEditModal
    ├── Input field
    ├── Validation
    ├── Error display
    └── Action buttons (Save, Cancel, Remove)
```

---

## 🔄 State Management Flow

```
User Click
    ↓
handleOpenEdit() → Set editingType
    ↓
Modal Opens
    ↓
User Enters URL
    ↓
handleSaveUrl()
    ├── Validate URL
    ├── Call API (updateProfileSocial)
    ├── Update local state (onProfileUpdate)
    └── Close modal
    ↓
Component Re-renders
    ├── URL now shows in SocialCard
    ├── Displays extracted username
    └── Ready for next edit
```

---

## 🎨 Tailwind Styling

All styling uses Tailwind CSS with a dark theme:
- **Background:** `bg-slate-900` with gradients
- **Borders:** `border-white/10` with hover state `white/20`
- **Text:** `text-white` for primary, `text-gray-400` for secondary
- **Icons:** Lucide React icons with `h-5 w-5` sizing
- **Animations:** Framer Motion for hover/tap effects

---

## ⚙️ Backend Requirements

The component expects the following API endpoints:

### GET `/api/users/profile/`
Returns current user profile
```json
{
  "id": 1,
  "username": "deepmhatre13",
  "full_name": "Deepam Mhatre",
  "github_url": "https://github.com/deepmhatre13",
  "linkedin_url": "https://linkedin.com/in/deepam-mhatre",
  "portfolio_url": "https://example.com"
}
```

### PUT `/api/users/profile/`
Updates profile fields (all fields are optional)
```json
{
  "github_url": "https://github.com/deepmhatre13"
}
```

Returns updated profile object.

---

## 🧪 Testing Integration

```jsx
// Mock API
vi.mock('@/api/profile', () => ({
  updateProfileSocial: vi.fn(() =>
    Promise.resolve({ github_url: 'https://github.com/test' })
  ),
}));

// Test component
render(
  <SocialLinks
    profile={{ github_url: null }}
    onProfileUpdate={vi.fn()}
  />
);
```

---

## 📝 Error Handling

All error scenarios are handled gracefully:
- ❌ Invalid URL format → "Please enter a valid URL"
- ❌ Platform mismatch → "Please enter a valid GitHub URL"
- ❌ API failure → "Failed to update profile" + server error
- ❌ Network error → Error toast or retry option

---

## 🚀 Performance Optimizations

- **useCallback** for memoized handlers
- **motion.div** for efficient animations
- **Lazy modal** rendering (only renders when editing)
- **Optimistic UI updates** for instant feedback
- **Minimal re-renders** with proper state isolation

---

## 🎯 Next Steps

1. **Customize placeholder text** in SOCIAL_CONFIG
2. **Adjust colors** in styling classes
3. **Update API endpoints** if different
4. **Add toasts** for success/error feedback
5. **Extend validation** (e.g., check if profile exists)
6. **Add analytics** tracking (e.g., click tracking)

---

## 📞 Support

For issues or questions:
1. Check URL parsing in `urlUtils.js`
2. Verify API endpoints match backend
3. Check console for validation errors
4. Ensure profile data structure matches expected fields
