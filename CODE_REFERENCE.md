# FaceFind Modern Dashboard - Code Reference & Examples

## 🎯 CSS Animation Examples

### Button Hover Animation
```css
.stButton > button[kind="primary"] {
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    box-shadow: 0 8px 20px rgba(14, 165, 233, 0.3);
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 32px rgba(14, 165, 233, 0.4);
    animation: buttonHoverPulse 0.6s ease-in-out;
}

@keyframes buttonHoverPulse {
    0%, 100% { box-shadow: 0 8px 20px rgba(14, 165, 233, 0.3); }
    50% { box-shadow: 0 12px 30px rgba(14, 165, 233, 0.5); }
}
```

### Page Entrance Animation
```css
.stMainBlockContainer {
    animation: fadeInUp 0.5s ease-out;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### Card Hover Animation
```css
[data-testid="stMetric"] {
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    border-radius: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

[data-testid="stMetric"]:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    border-color: #0EA5E9;
}
```

### Heading Slide-Down
```css
h1, h2, h3, h4, h5, h6 {
    animation: slideInDown 0.4s ease-out;
}

@keyframes slideInDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### Input Focus Glow
```css
.stTextInput input:focus,
.stSelectbox [data-baseweb="select"]:focus {
    border-color: #0EA5E9;
    box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
    transition: all 0.3s ease;
}
```

## 🎨 Gradient Examples

### Primary Gradient (Buttons)
```css
background: linear-gradient(135deg, #0EA5E9, #8B5CF6);
background-size: 200% auto;
```

### Scrollbar Gradient
```css
::-webkit-scrollbar-thumb {
    background: linear-gradient(to bottom, #0EA5E9, #8B5CF6);
    border-radius: 10px;
}
```

### Hero Section Gradient
```css
.facefind-header {
    background: linear-gradient(135deg, #0EA5E9 0%, #3B82F6 40%, #8B5CF6 100%);
    padding: 2.5rem;
    border-radius: 24px;
}
```

## 📝 Python Code Examples

### Modernized Form Layout
```python
with st.form("user_login_form", border=False):
    st.markdown("<div style='padding: 0.5rem 0;'></div>", unsafe_allow_html=True)
    
    email = st.text_input(
        "Email Address",
        placeholder="you@example.com",
        key="login_email"
    )
    password = st.text_input(
        "Password",
        type="password",
        placeholder="••••••••",
        key="login_password"
    )
    
    st.markdown("<div style='padding: 0.5rem 0;'></div>", unsafe_allow_html=True)
    
    col_space, col_btn = st.columns([0.15, 0.85])
    with col_btn:
        submitted = st.form_submit_button(
            "Sign In",
            use_container_width=True,
            type="primary"
        )
```

### Modern Container with Animation
```python
st.markdown("""
<div style='text-align:center; padding-bottom: 1.5rem; animation: slideInDown 0.5s ease-out;'>
    <h2 style='font-size: 2rem; font-weight: 800; color: #111827; margin: 0;'>
        🔍 Find My Photos
    </h2>
    <p style='color: #4B5563; font-size: 0.95rem; margin-top: 0.5rem; font-weight: 500;'>
        Upload a photo and AI will find you across all event galleries
    </p>
</div>
""", unsafe_allow_html=True)
```

### Success Message with Animation
```python
st.markdown("""
<div style='
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 12px;
    padding: 0.75rem;
    text-align: center;
    color: #059669;
    font-weight: 600;
    font-size: 0.9rem;
    margin-top: 1rem;
    animation: slideInDown 0.3s ease-out;
'>
    ✅ Photo ready for search
</div>
""", unsafe_allow_html=True)
```

### Metrics with Animations
```python
col1, col2, col3, col4 = st.columns(4, gap="small")
with col1:
    st.metric("🖼️ Total Photos", stats["total_photos"])
with col2:
    st.metric("👥 Registered Users", stats["total_users"])
with col3:
    st.metric("🔍 Total Searches", stats["total_searches"])
with col4:
    st.metric("✅ Face Matches", stats["total_matches"])
```

### Modern Tab Layout
```python
tabs = st.tabs([
    "🔍 Find My Photos",
    "📚 My Library",
    "🗂️ Browse by Scene"
])
with tabs[0]:
    _render_search_tab()
with tabs[1]:
    _render_library_tab()
with tabs[2]:
    _render_browse_tab()
```

## 🎯 CSS Variable System

### Color Variables
```css
:root {
    --primary: #0EA5E9;
    --primary-dark: #0284C7;
    --secondary: #8B5CF6;
    --text-primary: #111827;
    --text-secondary: #4B5563;
    --bg-primary: #FFFFFF;
    --bg-secondary: #F9FAFB;
    --border: #E5E7EB;
    --border-light: #F3F4F6;
}
```

### Using Variables
```css
button {
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: var(--text-primary);
    border-color: var(--border);
}

:hover {
    border-color: var(--primary);
    color: var(--primary);
}
```

## 🔧 Common Customizations

### Change Primary Color to Red
```css
:root {
    --primary: #EF4444;
    --primary-dark: #DC2626;
    --secondary: #F87171;
}
```

### Make Buttons Larger
```css
.stButton > button {
    padding: 1rem 2.5rem !important;
    font-size: 1.1rem !important;
    border-radius: 16px !important;
}
```

### Faster Animations
```css
.stMainBlockContainer {
    animation: fadeInUp 0.3s ease-out !important;
}

.stButton > button:hover {
    animation: buttonHoverPulse 0.3s ease-in-out !important;
}
```

### Disable Animations
```css
* {
    animation: none !important;
    transition: none !important;
}
```

## 📊 Animation Timing Guide

| Duration | Use Case |
|----------|----------|
| 200ms | Quick micro-interactions |
| 300ms | Button hover, tab switch |
| 400ms | Heading entrance |
| 500ms | Page content fade in |
| 600ms | Button pulse effect |

**Note**: Always use 300-600ms for smooth, perceptible animations.

## 🎬 Animation Easing Functions

```css
/* Linear */
cubic-bezier(0, 0, 1, 1)

/* Ease-out (recommended for entrance) */
cubic-bezier(0, 0, 0.2, 1)

/* Ease-in-out (recommended for hover) */
cubic-bezier(0.34, 1.56, 0.64, 1)

/* Smooth cubic */
cubic-bezier(0.4, 0, 0.2, 1)
```

## 🌈 Color Palette Reference

```
Blues:
  Light:   #0EA5E9 (primary)
  Medium:  #3B82F6
  Dark:    #0284C7 (primary-dark)

Purples:
  Main:    #8B5CF6 (secondary)
  Dark:    #6D28D9

Grays:
  White:     #FFFFFF
  Off-white: #F9FAFB
  Light:     #F3F4F6
  Medium:    #E5E7EB
  Text:      #4B5563
  Dark:      #111827
```

## 🔐 Best Practices

### DO ✅
- Use CSS variables for colors
- Keep animations 300-600ms
- Use transforms (not position) for animations
- Test animations on slower devices
- Provide fallbacks for older browsers
- Use proper contrast ratios

### DON'T ❌
- Don't animate more than 5 elements per page
- Don't use animations > 800ms (feels slow)
- Don't use color-based animations only
- Don't forget focus states for accessibility
- Don't ignore performance on mobile
- Don't use too many different animation styles

## 📱 Responsive Tips

```css
/* Mobile-first approach */
@media (max-width: 768px) {
    .stMainBlockContainer {
        padding-top: 1rem !important;
    }
    
    .stButton > button {
        padding: 0.6rem 1.2rem !important;
    }
}
```

## 🚀 Performance Optimization

### GPU-Accelerated Properties
```css
/* Smooth on GPU */
transform: translateY(-3px);     ✅
opacity: 0.9;                    ✅
box-shadow: ...;                 ⚠️ Sometimes

/* Can cause jank */
top: 3px;                        ❌
left: 0;                         ❌
width: 100%;                     ❌
```

## 📚 Additional Resources

- CSS Easing Guide: [cubic-bezier.com](https://cubic-bezier.com/)
- Color Tools: [coolors.co](https://coolors.co/)
- Web Animation Docs: [developer.mozilla.org](https://developer.mozilla.org/en-US/docs/Web/CSS/animation)

---

**Pro Tip**: Copy and modify these examples to create your own custom animations!
