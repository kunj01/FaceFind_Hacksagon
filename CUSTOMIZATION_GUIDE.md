# FaceFind Modern Dashboard - Customization Guide

## 🎨 Quick Customization Tips

### 1. Change Primary Color

To change the primary blue to a different color:

**In `app.py` CSS section, change:**
```css
--primary: #0EA5E9;     /* Change this color */
--primary-dark: #0284C7; /* Change this to darker version */
```

**Example color combinations:**
- Red theme: `#EF4444` (primary), `#DC2626` (dark)
- Green theme: `#10B981` (primary), `#059669` (dark)
- Orange theme: `#F97316` (primary), `#EA580C` (dark)
- Pink theme: `#EC4899` (primary), `#BE185D` (dark)

### 2. Adjust Animation Speed

To make animations faster/slower, modify these in `app.py`:

```css
/* Faster animations (uncomment these instead) */
slideInDown       { animation: slideInDown 0.2s ease-out !important; }
fadeInUp          { animation: fadeInUp 0.3s ease-out !important; }
scaleIn           { animation: scaleIn 0.2s ease-out !important; }

/* Or slower animations */
slideInDown       { animation: slideInDown 0.6s ease-out !important; }
fadeInUp          { animation: fadeInUp 0.7s ease-out !important; }
scaleIn           { animation: scaleIn 0.6s ease-out !important; }
```

### 3. Change Font

To use a different font family:

```css
/* Replace 'Inter' with any Google Font */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif !important;
}
```

**Popular alternatives:**
- `Poppins` - Modern, rounded
- `Montserrat` - Clean, geometric
- `Roboto` - Neutral, professional
- `Work Sans` - Friendly, modern
- `IBM Plex Sans` - Corporate, technical

### 4. Increase/Decrease Padding & Spacing

**For larger spacing:**
```css
.stMainBlockContainer {
    padding-top: 3rem !important;      /* was 2rem */
    padding-bottom: 3rem !important;
}
```

**For smaller spacing:**
```css
.stMainBlockContainer {
    padding-top: 1rem !important;      /* was 2rem */
    padding-bottom: 1rem !important;
}
```

### 5. Adjust Border Radius (Roundness)

**More rounded (softer look):**
```css
.stButton > button     { border-radius: 16px !important; }
[data-testid="stMetric"] { border-radius: 20px !important; }
.stTextInput input     { border-radius: 16px !important; }
```

**Less rounded (sharper look):**
```css
.stButton > button     { border-radius: 8px !important; }
[data-testid="stMetric"] { border-radius: 12px !important; }
.stTextInput input     { border-radius: 8px !important; }
```

### 6. Change Button Style

**For more prominent buttons:**
```css
.stButton > button[kind="primary"] {
    padding: 1rem 2.5rem !important;     /* was 0.7rem 1.8rem */
    font-size: 1.1rem !important;        /* was 0.95rem */
    border-radius: 16px !important;      /* was 12px */
}
```

**For subtle buttons:**
```css
.stButton > button[kind="primary"] {
    padding: 0.6rem 1.5rem !important;
    font-size: 0.85rem !important;
    border-radius: 8px !important;
}
```

### 7. Disable Animations (for accessibility)

To disable all animations:

```css
* {
    animation: none !important;
    transition: none !important;
}
```

Or for specific elements:
```css
.stButton > button {
    transition: none !important;
}

@keyframes fadeInUp { from {} to {} }
@keyframes slideInDown { from {} to {} }
@keyframes scaleIn { from {} to {} }
```

### 8. Change Gradient Colors

**Current gradient (Primary button):**
```css
background: linear-gradient(135deg, #0EA5E9, #8B5CF6) !important;
```

**Custom gradients:**
```css
/* Sunset gradient */
background: linear-gradient(135deg, #FF6B6B, #FFA500) !important;

/* Ocean gradient */
background: linear-gradient(135deg, #00D4FF, #0099FF) !important;

/* Forest gradient */
background: linear-gradient(135deg, #10B981, #059669) !important;

/* Organic gradient */
background: linear-gradient(135deg, #8B5CF6, #D946EF) !important;
```

### 9. Adjust Shadow Depth

**For subtle shadows (flat design):**
```css
[data-testid="stMetric"] {
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}
```

**For prominent shadows (elevated design):**
```css
[data-testid="stMetric"] {
    box-shadow: 0 20px 40px rgba(0,0,0,0.2) !important;
}
```

### 10. Change Button Hover Effect

**More pronounced hover:**
```css
.stButton > button[kind="primary"]:hover {
    transform: translateY(-6px) scale(1.05) !important;
    box-shadow: 0 24px 48px rgba(14, 165, 233, 0.5) !important;
}
```

**Subtle hover:**
```css
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2) !important;
}
```

## 🎯 Common Theme Presets

### Dark Mode (Future Implementation)
```css
--bg-primary: #1F2937;
--bg-secondary: #111827;
--text-primary: #FFFFFF;
--text-secondary: #D1D5DB;
--border: #374151;
```

### High Contrast (Accessibility)
```css
--primary: #0000FF;
--text-primary: #000000;
--bg-primary: #FFFFFF;
--border: #000000;
```

### Warm Palette
```css
--primary: #EA580C;
--secondary: #D97706;
--bg-secondary: #FEF3C7;
```

### Cool Palette
```css
--primary: #06B6D4;
--secondary: #0284C7;
--bg-secondary: #ECFDF5;
```

## 📱 Responsive Adjustments

To adjust spacing for mobile only:

```css
@media (max-width: 768px) {
    .stMainBlockContainer {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    .stButton > button {
        padding: 0.6rem 1.2rem !important;
    }
}
```

## 🔧 Common Issues & Solutions

### Issue: Animations too slow/fast
**Solution**: Adjust timing in CSS (200ms-600ms range is good)

### Issue: Colors don't match
**Solution**: Use CSS variables, change in `:root` section

### Issue: Spacing too cramped
**Solution**: Increase padding/margin values (1rem = 16px)

### Issue: Buttons not interactive looking
**Solution**: Add more pronounced hover effects

### Issue: Mobile layout broken
**Solution**: Check column gaps and adjust for smaller screens

## 🎨 Recommended Tools

- **Color Picker**: [Coolors.co](https://coolors.co/)
- **Gradient Generator**: [Gradient.style](https://gradient.style/)
- **Font Selector**: [Google Fonts](https://fonts.google.com/)
- **Animation Easing**: [Cubic Bezier](https://cubic-bezier.com/)
- **Contrast Checker**: [WCAG Contrast](https://webaim.org/resources/contrastchecker/)

## 📊 Performance Tips

1. **Reduce animation count**: Disable animations on low-end devices
2. **Use GPU acceleration**: Transform and opacity animate smoothly
3. **Limit shadow effects**: Heavy shadows reduce performance
4. **Minimize transitions**: Use 300-600ms, not longer
5. **Remove unused keyframes**: Clean up CSS

## 🎯 A/B Testing Tips

To test different designs:

1. Create alternate CSS sections
2. Use Streamlit session state to toggle
3. Compare user engagement metrics
4. Measure animation performance

**Example:**
```python
if st.sidebar.checkbox("Use Dark Theme"):
    st.markdown("""<style>/* dark mode CSS */</style>""")
else:
    st.markdown("""<style>/* light mode CSS */</style>""")
```

## 🚀 Next Steps for Enhancement

1. **Dark Mode**: Duplicate CSS with dark colors
2. **Theme Switcher**: Add sidebar toggle for themes
3. **Custom Branding**: Update logo and colors
4. **Advanced Animations**: Add page transitions
5. **Accessibility**: Add ARIA labels and keyboard navigation
6. **Performance**: Optimize animations for slower devices

---

**Pro Tip**: Make changes in small increments and test in browser before finalizing!
