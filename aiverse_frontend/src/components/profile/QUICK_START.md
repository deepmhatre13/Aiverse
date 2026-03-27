# 🚀 Quick Start Guide - Social Links Component

Get the component running in **2 minutes**.

---

## ⚡ Step 1: Import the Component

In your profile page file:

```jsx
import SocialLinks from '@/components/profile/SocialLinks';
```

---

## ⚡ Step 2: Add Component to Your Page

```jsx
function ProfilePage() {
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    // Fetch profile from API
    fetchProfile().then(setProfile);
  }, []);

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* Other profile sections */}
      
      <SocialLinks 
        profile={profile}
        onProfileUpdate={setProfile}
      />
    </div>
  );
}
```

---

## ⚡ Step 3: Ensure Backend is Ready

Your backend must have these endpoints:

### `GET /api/users/profile/`
Returns profile object with social URLs

### `PUT /api/users/profile/`
Updates profile fields

**Expected Profile Object:**
```js
{
  github_url: "https://github.com/username",
  linkedin_url: "https://linkedin.com/in/name",
  portfolio_url: "https://example.com"
}
```

---

## ✅ That's It!

The component is now fully functional:

- ✅ Displays social links
- ✅ Shows clean usernames (not raw URLs)
- ✅ Click to open links
- ✅ Click to edit
- ✅ Validates URLs
- ✅ Saves to API
- ✅ Updates in real-time

---

## 🎨 Optional: Customize Styling

The component uses Tailwind. Customize by editing these classes in `SocialLinks.jsx`:

**Connected Card Background:**
```jsx
className={`bg-gradient-to-br from-slate-900 to-slate-800 ...`}
```

**Hover Border Color:**
```jsx
className={`hover:border-white/20 ...`}
```

**Text Color:**
```jsx
className={`text-gray-400 ...`}
```

---

## 📦 All Files Location

```
src/
├── components/profile/
│   ├── SocialLinks.jsx              ← Main component
│   ├── SocialEditModal.jsx          ← Edit modal
│   ├── SocialLinks.test.jsx         ← Tests
│   ├── SocialLinks.examples.jsx     ← Examples
│   ├── SOCIAL_LINKS_README.md       ← Full docs
│   └── IMPLEMENTATION_SUMMARY.md    ← Overview
├── api/
│   └── profile.js                   ← API service
└── lib/
    └── urlUtils.js                  ← URL utilities
```

---

## 🧪 Test It

```bash
# Run tests
npm test SocialLinks

# Should see all tests passing
```

---

## 🐛 Troubleshooting

### Component Not Showing?
- [ ] Import statement correct?
- [ ] Profile data passed in?
- [ ] Check browser console for errors

### URLs Not Updating?
- [ ] Backend endpoint returns 200?
- [ ] Check Network tab in dev tools
- [ ] See error message in component?

### Modal Not Opening?
- [ ] Dialog component imported?
- [ ] Check browser console

### URLs Not Extracted Correctly?
- [ ] Check urlUtils.js functions
- [ ] Verify URL format is correct
- [ ] Test with `getDisplayText()` directly

---

## 📱 Mobile Testing

The component is fully responsive:
- Mobile: `grid-cols-1`
- Tablet: `md:grid-cols-2`
- Desktop: `xl:grid-cols-3`

Test on different screen sizes ✅

---

## 🎯 Next: Advanced Features

Once basic integration works, you can:

1. **Add Toast Notifications**
   ```jsx
   const handleProfileUpdate = (profile) => {
     setProfile(profile);
     toast({ title: 'Profile updated!' });
   };
   ```

2. **Add Loading Skeleton**
   ```jsx
   if (isLoading) return <SocialLinksSkeleton />;
   ```

3. **Customize Error Messages**
   - Edit `SocialEditModal.jsx` validation messages
   - Or extend `urlUtils.js` validation logic

4. **Add Analytics Tracking**
   ```jsx
   window.gtag?.('event', 'social_link_click', {
     platform: type
   });
   ```

---

## 📞 Need Help?

1. Read [SOCIAL_LINKS_README.md](./SOCIAL_LINKS_README.md) for full documentation
2. Check [SocialLinks.examples.jsx](./SocialLinks.examples.jsx) for usage patterns
3. Look at [SocialLinks.test.jsx](./SocialLinks.test.jsx) for test examples
4. Check browser console for specific errors

---

## ✨ Features Summary

| Feature | Status |
|---------|--------|
| Display clean usernames | ✅ |
| Click to open links | ✅ |
| Edit modal | ✅ |
| URL validation | ✅ |
| API integration | ✅ |
| Error handling | ✅ |
| Loading states | ✅ |
| Mobile responsive | ✅ |
| Keyboard shortcuts | ✅ |
| Smooth animations | ✅ |

---

## 🚀 You're Ready!

Start using the component now. It's production-ready and fully featured.

Enjoy! 🎉
