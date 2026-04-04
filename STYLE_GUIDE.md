# FaceFind Modern Dashboard - Style Guide & Reference

## 🎨 Color Palette

```
Primary Blue:     #0EA5E9  (Sky Blue - Main Actions)
Primary Dark:     #0284C7  (Darker shade for hover)
Secondary:        #8B5CF6  (Purple - Accents)
Text Primary:     #111827  (Deep Gray/Black)
Text Secondary:   #4B5563  (Medium Gray)
Background:       #FFFFFF  (White - Cards)
Background Light: #F9FAFB  (Off-white - Pages)
Border:           #E5E7EB  (Light Gray)
Border Light:     #F3F4F6  (Lighter Gray)
```

## 📐 Spacing System

```
Small:    0.5rem  (8px)
Base:     1rem    (16px)
Medium:   1.5rem  (24px)
Large:    2rem    (32px)
XL:       2.5rem  (40px)
```

## 🔤 Typography

- **Font Family**: Inter (sans-serif)
- **Heading Weights**: 700-800 (Bold/Extra Bold)
- **Body Weight**: 400-600 (Regular/Semi-bold)
- **Heading Size**: 2-2.5rem
- **Body Size**: 0.95-1rem
- **Line Height**: 1.5

## 🎯 Border Radius

- **Small**: 10px (input fields, pills)
- **Medium**: 12px (buttons, small cards)
- **Large**: 16px (metric cards, containers)
- **XL**: 20-24px (hero sections, hero cards)

## ✨ Animations

### Entrance Animations
```css
slideInDown:  400ms ease-out (headings, sidebar)
fadeInUp:     500ms ease-out (page content)
scaleIn:      400-600ms ease-out (cards, metrics)
```

### Interaction Animations
```css
Hover Lift:       300ms cubic-bezier (3px up)
Glow Pulse:       600ms ease-in-out (button hover)
Scale:            300ms cubic-bezier (1.04x on hover)
Color Change:     300ms ease (text, border colors)
```

## 🔘 Button Styles

### Primary Button
- Background: Linear gradient (Sky Blue → Purple)
- Padding: 0.7rem 1.8rem
- Border-radius: 12px
- Font: 600 weight, 0.95rem
- Hover: Lift (-3px), enhanced glow
- Transition: 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)

### Secondary Button
- Background: White
- Border: 2px solid (Light Gray)
- Padding: 0.7rem 1.8rem
- Border-radius: 12px
- Hover: Color change to Primary Blue, lift (-2px)

## 📊 Card Styles

### Metric Cards
- Background: White
- Border: 1px solid Light Gray
- Border-radius: 16px
- Padding: 1.25rem
- Shadow: Light (2px 8px)
- Hover: Lift (-6px), darker shadow

### Container Cards
- Border: 1px solid Light Gray
- Border-radius: 16-20px
- Padding: Varies
- Animation: Scale-in on load

## 🎭 Tab Styles

- Background: Transparent
- Active: Underline (3px bottom border, Primary Blue)
- Inactive: Light background on hover
- Transition: 300ms smooth

## 📝 Input Fields

- Border: 1px solid Light Gray
- Border-radius: 12px
- Focus: Blue border + glow (3px rgba)
- Background: White
- Transition: Smooth 300ms

## 🌈 Gradient Usage

### Primary Gradient
```css
linear-gradient(135deg, #0EA5E9, #8B5CF6)
```
Used on: Primary buttons, hero header

### Light Gradient
```css
linear-gradient(to right, #0EA5E9, #8B5CF6)
```
Used on: Progress bars, scrollbars

## 📱 Responsive Breakpoints

- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

All layouts use Streamlit's responsive column system.

## 🎯 Hover Effects Reference

| Element | Effect | Duration |
|---------|--------|----------|
| Primary Button | Lift + Glow Pulse | 300ms + 600ms |
| Secondary Button | Lift + Color Change | 300ms |
| Metric Card | Lift + Shadow Enhance | 300ms |
| Image | Scale + Lift | 300ms |
| Tab | Background Color | 300ms |
| Link | Color Change | 300ms |

## 🔦 Shadow System

- **Small**: `0 2px 8px rgba(0,0,0,0.06)`
- **Medium**: `0 8px 16px rgba(0,0,0,0.12)`
- **Large**: `0 12px 24px rgba(0,0,0,0.15)`
- **Glow**: Special color-based shadows for buttons

## 💫 Message Styles

### Success (Green)
- Background: `rgba(16, 185, 129, 0.1)` (10% opacity)
- Border: `rgba(16, 185, 129, 0.3)` (30% opacity)

### Error (Red)
- Background: `rgba(239, 68, 68, 0.1)`
- Border: `rgba(239, 68, 68, 0.3)`

### Warning (Orange)
- Background: `rgba(245, 158, 11, 0.1)`
- Border: `rgba(245, 158, 11, 0.3)`

### Info (Blue)
- Background: `rgba(14, 165, 233, 0.1)`
- Border: `rgba(14, 165, 233, 0.3)`

All with smooth slide-in animation and backdrop blur.

## 🎬 Complete Animation Examples

### Page Load
```
1. Container appears (fadeInUp 500ms)
2. Heading slides down (slideInDown 400ms)
3. Cards scale in (scaleIn 400-600ms staggered)
```

### Button Interaction
```
1. User hovers: Button lifts 3px (300ms)
2. Glow pulses (600ms loop)
3. Shine effect sweeps across (400ms)
4. On click: Brief scale down then back
```

### Navigation
```
1. Tab change: Underline animates to new position
2. Content fades in (fadeInUp 500ms)
3. Cards appear in sequence (scaleIn 300-600ms)
```

## 📐 Form Layout

- **Column Gap**: Small (12px) to Medium (16px)
- **Row Gap**: Medium (16px) to Large (24px)
- **Label Spacing**: 0.5rem above inputs
- **Button Spacing**: 1rem above submit button

## 🎯 Accessibility Features

- ✅ Focus states with visible outlines
- ✅ Sufficient color contrast (WCAG AA)
- ✅ Larger touch targets (44px minimum)
- ✅ Clear visual hierarchy
- ✅ Smooth animations (no 500ms+ delays)
- ✅ Feedback on interactions
