# 🎨 Social Links Visual Reference Guide

Complete visual documentation of all UI states, interactions, and design patterns.

---

## 📱 Component Layout

### Desktop (xl:grid-cols-3)
```
┌────────────────────────────────────────────────────────────┐
│ Social & Presence                                           │
│ Connect your professional profiles to showcase your work   │
├────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ GITHUB    ✏ │  │ LINKEDIN  ✏ │  │ PORTFOLIO   │        │
│  │ 🐙 deepm.. │  │ 🔗 deepam.. │  │ 🌐 Visit... │        │
│  │          ⤴ │  │          ⤴ │  │          ⤴ │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└────────────────────────────────────────────────────────────┘
```

### Tablet (md:grid-cols-2)
```
┌────────────────────────────────┐
│ Social & Presence              │
├────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐
│ │ GITHUB    ✏ │ │ LINKEDIN  ✏ │
│ │ 🐙 deepm.. │ │ 🔗 deepam.. │
│ │          ⤴ │ │          ⤴ │
│ └─────────────┘ └─────────────┘
│ ┌─────────────┐
│ │ PORTFOLIO   │
│ │ 🌐 Visit... │
│ │          ⤴ │
│ └─────────────┘
└────────────────────────────────┘
```

### Mobile (grid-cols-1)
```
┌────────────────┐
│ Social &       │
│ Presence       │
├────────────────┤
│ ┌────────────┐ │
│ │ GITHUB   ✏ │ │
│ │ 🐙 deepm. │ │
│ │         ⤴ │ │
│ └────────────┘ │
│ ┌────────────┐ │
│ │ LINKEDIN ✏ │ │
│ │ 🔗 deepa.  │ │
│ │         ⤴ │ │
│ └────────────┘ │
│ ┌────────────┐ │
│ │PORTFOLIO   │ │
│ │ 🌐 Visit.. │ │
│ │         ⤴ │ │
│ └────────────┘ │
└────────────────┘
```

---

## 🎨 Card States

### STATE 1: Connected (URL Exists)

```
VISUAL:
┌─────────────────────────────────────────┐
│ GITHUB                                ✏  │  ← Edit button (appears on hover)
│ 🐙 deepmhatre13                       ⤴  │  ← External link button
└─────────────────────────────────────────┘
   ↑
   └─ Entire card is clickable
      Hover: Slight lift + border highlight
      Click: Opens URL in new tab

COLORS:
- Background: bg-gradient-to-br from-slate-900 to-slate-800
- Border: border-white/10
- Hover Border: border-white/20
- Text (username): text-white font-medium
- Icons: text-white/70 → text-white (on hover)
- Button hover: text-gray-200 bg-white/10

INTERACTION:
Click Card       → window.open(url, "_blank")
Click Edit Icon  → Open modal
Click Link Icon  → window.open(url, "_blank")
Hover            → Card lifts (y: -2px)
```

### STATE 2: Empty (No URL)

```
VISUAL:
┌─────────────────────────────────────────┐
│ GITHUB                                    │
│ 🐙 Add GitHub profile                    │
└─────────────────────────────────────────┘
   ↑
   └─ No edit button
      Click anywhere to edit

COLORS:
- Background: bg-slate-900/50
- Border: border-white/5
- Hover Border: border-white/10
- Text: text-gray-400
- Icons: text-white/70 (muted)
- No external link button

INTERACTION:
Click Card  → Open edit modal
Hover       → Border highlights only (no lift)
```

### STATE 3: Hover (Connected)

```
BEFORE HOVER:
┌─────────────────────────────────────────┐
│ GITHUB                                    │
│ 🐙 deepmhatre13                       ⤴  │
└─────────────────────────────────────────┘

AFTER HOVER:
┌─────────────────────────────────────────┐  ↑ Lifts up (y: -2px)
│ GITHUB                                ✏  │  ← Edit icon appears
│ 🐙 deepmhatre13                       ⤴  │  ← Link icon brightens
└─────────────────────────────────────────┘  ↑ Border brightens
   ↑ Border: white/10 → white/20
   ↑ Cursor: pointer
   ↑ Duration: 200ms smooth transition
```

### STATE 4: Loading (While Saving)

```
VISUAL:
┌──────────────────────────────────────────┐
│ GitHub Profile              [Close ✕]    │
│ Add your GitHub profile to showcase      │
├──────────────────────────────────────────┤
│ Profile URL                              │
│ [https://github.com/... ────]            │  (faded/disabled)
│                                          │
├──────────────────────────────────────────┤
│ [Remove]                  [Cancel] [↻ ..] │  ← Spinner on Save
│                                    ↑ disabled  
└──────────────────────────────────────────┘

DETAILS:
- Input: disabled, opacity reduced
- Buttons: disabled
- Save Button: Shows spinner + "Saving..."
- Cannot interact while saving
- Duration: Until API responds
```

### STATE 5: Error State

```
VISUAL:
┌──────────────────────────────────────────┐
│ GitHub Profile              [Close ✕]    │
│ Add your GitHub profile to showcase      │
├──────────────────────────────────────────┤
│ Profile URL                              │
│ [https://github.com/... ────]            │
│                                          │
│ ❌ Please enter a valid GitHub URL       │  ← Error message
│                                          │
├──────────────────────────────────────────┤
│ [Remove]                  [Cancel] [Save] │
└──────────────────────────────────────────┘

DETAILS:
- Error box: p-3 bg-red-900/20 border border-red-900/50
- Error text: text-sm text-red-200
- Input border: Subtle red tint
- User can retry after fixing
```

---

## 🎬 Interaction Sequences

### Sequence 1: Adding a New Link

```
1. INITIAL STATE
   ┌────────────────────┐
   │ GITHUB             │
   │ 🐙 Add GitHub...   │  ← Empty state
   └────────────────────┘

2. USER CLICKS CARD
   ↓ Modal opens

3. MODAL APPEARS
   ┌──────────────────────────────┐
   │ GitHub Profile            ✕  │
   │ Add your GitHub profile     │
   ├──────────────────────────────┤
   │ Profile URL                  │
   │ [https://github.com/...]     │
   │                              │
   ├──────────────────────────────┤
   │                  [Cancel] [Save]
   └──────────────────────────────┘

4. USER TYPES URL
   ┌──────────────────────────────┐
   │ GitHub Profile            ✕  │
   ├──────────────────────────────┤
   │ [https://github.com/deepm.]  │  ← User typing
   │                              │
   │ Example: https://github.com/deepm... │
   └──────────────────────────────┘

5. USER CLICKS SAVE
   ↓ Validation runs ✓
   ↓ API call (/api/users/profile/)
   ↓ ID: github_url: "https://github.com/deepm..."

6. SUCCESS
   ┌────────────────────┐
   │ GITHUB           ✏ │  ← Updated state
   │ 🐙 deepm...      ⤴ │
   └────────────────────┘
   Modal closes automatically
```

### Sequence 2: Editing Existing Link

```
1. INITIAL STATE
   ┌────────────────────┐
   │ GITHUB           ✏ │
   │ 🐙 deepm...      ⤴ │  ← Connected
   └────────────────────┘

2. USER HOVERS
   ┌────────────────────┐
   │ GITHUB           ✏ │  ← Edit icon visible
   │ 🐙 deepm...      ⤴ │
   └────────────────────┘
   Subtle lift

3. USER CLICKS EDIT ICON
   ↓ Modal opens with current URL

4. MODAL SHOWS CURRENT URL
   ┌──────────────────────────────┐
   │ GitHub Profile            ✕  │
   ├──────────────────────────────┤
   │ [https://github.com/deepm...]│  ← Pre-filled
   │                              │
   │ [Remove]        [Cancel] [Save]
   └──────────────────────────────┘

5. USER EDITS AND SAVES
   ↓ Validation ✓
   ↓ API call
   ↓ Success

6. CARD UPDATES
   ┌────────────────────┐
   │ GITHUB           ✏ │
   │ 🐙 newusername   ⤴ │  ← New username shown
   └────────────────────┘
```

### Sequence 3: Removing a Link

```
1. USER OPENS EDIT MODAL
2. CLICKS "REMOVE" BUTTON
   ↓ Confirmation? (optional)
   ↓ API call with null value
   ↓ Clears field

3. CARD REVERTS TO EMPTY
   ┌────────────────────┐
   │ GITHUB             │  ← Back to empty state
   │ 🐙 Add GitHub...   │
   └────────────────────┘
```

### Sequence 4: Opening a Link

```
OPTION A: Click card
┌────────────────────┐
│ GITHUB           ✏ │
│ 🐙 deepm...      ⤴ │
└────────────────────┘
      ✓ Clicks card
      ↓ window.open(url, '_blank')
      ↓ New tab opens

OPTION B: Click external link icon
┌────────────────────┐
│ GITHUB           ✏ │
│ 🐙 deepm...      ⤴ │  ← Click this
└────────────────────┘
      ✓ Clicks ⤴ button
      ↓ window.open(url, '_blank')
      ↓ New tab opens
```

---

## 🎨 Animation Details

### Card Entrance (Page Load)
```
INITIAL:   opacity: 0, y: 16px
ANIMATE:   opacity: 1, y: 0
DURATION:  350ms
EASING:    ease-out
DELAY:     50ms per section
```

### Hover Effect (Connected State)
```
INITIAL:   y: 0
HOVER:     y: -2px
TAP:       y: 0
DURATION:  200ms
EASING:    spring
```

### Modal Appearance
```
INITIAL:   scale: 0.95, opacity: 0
ANIMATE:   scale: 1, opacity: 1
DURATION:  200ms
EASING:    ease-out
```

### Icon Animations
```
Edit/Link buttons:
HOVER:     scale: 1.1 (110%)
TAP:       scale: 0.95 (95%)
DURATION:  100ms
```

---

## 🎨 Color Palette

### Connected Cards
```
Background:  from-slate-900 to-slate-800 (gradient)
Border:      border-white/10 (10% opacity white)
Hover:       border-white/20 (20% opacity, brighter)
Text:        text-white (primary)
Subtext:     text-gray-400 (secondary)
Icons:       text-white/70 → text-white (on hover)
Button Hover: bg-white/10 text-gray-200
```

### Empty Cards
```
Background:  bg-slate-900/50 (50% opacity)
Border:      border-white/5 (5% opacity white)
Hover:       border-white/10 (10% opacity)
Text:        text-gray-400 (muted)
Icons:       text-white/70 (faded)
No lift effect
```

### Edit Modal
```
Background:  bg-background (dialog default)
Border:      border border-input
Text Input:  border-input bg-background
Error Box:   bg-red-900/20 border-red-900/50
Error Text:  text-red-200
Ok Box:      bg-green-900/20 border-green-900/50 (if success)
```

---

## 📏 Sizing

### Icons
```
Card icon:           h-5 w-5
Edit/Link buttons:   h-4 w-4 (smaller)
Modal icons:         h-4 w-4
```

### Text
```
Label (GITHUB):      text-xs font-semibold
Username:            text-sm font-medium
Placeholder:         text-sm
Helper text:         text-xs text-gray-400
Modal label:         text-sm font-medium
```

### Spacing
```
Card padding:        p-4
Card gap:            space-y-2
Section gap:         space-y-4
Modal padding:       p-6
Grid gap:            gap-4
Button gap:          gap-2
```

### Borders
```
Radius:              rounded-xl (8-16px depending on element)
Border width:        1px (default)
```

---

## 🎯 States Summary Table

| State | Background | Border | Text | Interactive | Edit Icon | Link Icon |
|-------|-----------|--------|------|-------------|-----------|-----------|
| Connected (normal) | slate-900 gradient | white/10 | white | ✓ cursor-pointer | ✓ on hover | ✓ visible |
| Connected (hover) | slate-900 gradient | white/20 | white | ✓ pointer | ✓ visible | ✓ bright |
| Empty | slate-900/50 | white/5 | gray-400 | ✓ default | ✗ none | ✗ none |
| Empty (hover) | slate-900/50 | white/10 | gray-400 | ✓ default | ✗ none | ✗ none |
| Loading | (in modal) | (disabled) | (disabled) | ✗ disabled | ✗ disabled | ✗ disabled |
| Error | (in modal) | red-900/50 | red-200 | ✓ retry | - | - |

---

## 🔄 Full Page State

### Complete Profile with All Links
```
┌──────────────────────────────────────────────────────┐
│ Social & Presence                                     │
│ Connect your professional profiles...                │
├──────────────────────────────────────────────────────┤
│ ┌──────────────────┐ ┌──────────────────────────────┐
│ │ GITHUB         ✏ │ │ LINKEDIN                   ✏ │
│ │ 🐙 deepmhatre13│ │ │ 🔗 deepam-mhatre          │
│ │             ⤴ │ │ │                         ⤴ │
│ └──────────────────┘ │ │ PORTFOLIO                  │
│                      │ │ 🌐 Visit Website        ⤴ │
│                      └──────────────────────────────┘
│ 
│ (Success message if just saved)
│ ✓ Profile updated successfully!
└──────────────────────────────────────────────────────┘
```

### Mixed State (Some Empty)
```
┌──────────────────────────────────────────────────────┐
│ Social & Presence                                     │
│ Connect your professional profiles...                │
├──────────────────────────────────────────────────────┤
│ ┌──────────────────┐ ┌──────────────────────────────┐
│ │ GITHUB         ✏ │ │ LINKEDIN                     │
│ │ 🐙 deepmhatre13│ │ │ 🔗 Add LinkedIn profile      │
│ │             ⤴ │ │ │                              │
│ └──────────────────┘ │ │ PORTFOLIO                    │
│                      │ │ 🌐 Add personal website     │
│                      └──────────────────────────────┘
└──────────────────────────────────────────────────────┘
```

---

## 🚀 Best Practices

✅ **Do:**
- Keep usernames short and readable (truncate if needed)
- Use consistent spacing
- Maintain animation smoothness
- Show loading states
- Display error messages clearly
- Use intuitive icons

❌ **Don't:**
- Show full URLs (defeats purpose)
- Make users scroll within component
- Use harsh colors
- Skip validation
- Forget keyboard shortcuts
- Ignore mobile responsiveness

---

## 🎯 Pixel-Perfect Reference

For developers implementing custom styling:

```jsx
// Connected Card Hover
borderColor: 'rgba(255, 255, 255, 0.2)'  // white/20
transform: 'translateY(-2px)'
transition: 'all 200ms ease-out'

// Icon on Hover
scale: 1.1
opacity: 1

// External Link Icon  
scale: 0.95
opacity: 0.5 → 1.0

// Modal Layout
maxWidth: '28rem'  // sm:max-w-md
padding: '24px'    // p-6
```

---

This visual reference covers every UI state, interaction, and design detail!
