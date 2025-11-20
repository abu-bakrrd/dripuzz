# E-Commerce Mobile Shop Design Guidelines

## Design Approach
**Reference-Based:** Wildberries-inspired card design adapted to minimal aesthetic for a mobile-first Telegram Mini App.

## Core Design Principles
- Flat, minimal design with focus on product imagery
- Customizable color palette through config
- Mobile-only interface (max 420px width)
- No hover effects, 3D elements, or complex animations
- Large touch targets (minimum 44px) for mobile usability
- Breathing space with generous padding

## Color Palette

### Customizable via config/settings.json
- **Background:** Customizable (default: #FEFEFE)
- **Primary Text:** Customizable (default: #2E2E2E)
- **Secondary Text:** Customizable (default: #7A7A7A)
- **Primary Accent:** Customizable for buttons and CTAs
- **Secondary Accent:** Customizable for alternative highlights
- **Borders:** Customizable (default: #EAEAEA)

## Typography
- **Font Families:** Inter, Poppins, or system sans-serif
- **Header:** 20-24px, semi-bold
- **Product Names:** 14-16px, medium weight
- **Price:** 16-18px, bold
- **Body Text:** 14px, regular
- **Buttons:** 14-16px, medium weight

## Layout System
**Spacing Primitives:** Use units of 2, 4, 8, 12, 16, 20, 24px for consistent rhythm

### Grid Structure
- **Product Cards:** 2-column grid layout
- **Card Spacing:** 8-12px gap between cards
- **Container Padding:** 16px horizontal, 12px vertical
- **Section Spacing:** 20-24px between major sections

## Component Library

### Header (Sticky Top)
- Compact height: 56-60px
- Left: Logo + Shop Name (from config)
- Right: Heart icon (favorites) + Cart icon
- Minimal shadow or subtle bottom border

### Horizontal Filter Bar (Scrollable)
- Positioned directly under header
- Single row with horizontal scroll
- **Elements:** Category chips (with icons) → Color circles → Price range (two inputs) → Sort options
- Chip design: Rounded (24px border-radius), 8px padding, subtle background when selected
- Touch-friendly: 36-40px min height

### Product Cards (Wildberries Style)
- **Aspect Ratio:** Square or 3:4 for product images
- **Border Radius:** 12-16px
- **Elements:**
  - Product image (full width, lazy loading, WebP format)
  - Heart icon (top-left overlay, fills with color on tap)
  - Product name (below image, 2-line max)
  - Price (bold, below name)
  - Cart button (bottom-right or full-width)
- **Card Shadow:** None or very subtle (0 1px 3px rgba(0,0,0,0.08))
- **Spacing:** 12px internal padding

### Product Detail Page
- **Image Gallery:** Swipeable carousel or dot-navigation
- **Layout:** Full-width images, content below
- **Action Buttons:** "Add to Cart" (primary accent color) + Heart (outline)
- **Button Height:** 48px minimum

### Shopping Cart
- **Item Cards:** Horizontal layout (image left, details right, controls far right)
- **Quantity Controls:** Circle +/- buttons (36px minimum)
- **Remove Item:** Trash icon (tap to delete, confirmation optional)
- **Sticky Footer:** Shows total price + checkout button

### Bottom Navigation (Optional)
- Fixed position: bottom of screen
- 4-5 items max
- Icons + labels
- Active state: Primary accent color

## Touch Interactions
- **Tap Areas:** Minimum 44x44px for all interactive elements
- **Ripple Effect:** Subtle ripple on tap (optional)
- **Loading States:** Skeleton screens for product grids
- **Pull to Refresh:** Optional for product lists
- **Swipe Gestures:** 
  - Horizontal swipe in image gallery
  - Swipe to delete cart items (optional)

## Performance
- **Image Optimization:** Use WebP format, lazy loading
- **Code Splitting:** Load sections on demand
- **Caching:** Cache product images and data
- **Fast Initial Load:** Under 2 seconds on 3G

## Accessibility
- **Color Contrast:** WCAG AA compliance
- **Touch Targets:** 44px minimum
- **Focus States:** Clear visual indicators
- **Screen Readers:** Proper ARIA labels

## Animation Guidelines
- **Subtle Transitions:** 200-300ms duration
- **Easing:** ease-in-out
- **Page Transitions:** Simple fade or slide
- **Avoid:** Complex animations, parallax effects

## Mobile Optimization
- **Viewport:** max-width: 420px
- **Safe Areas:** Account for notches and bottom bars
- **Orientation:** Portrait only (lock orientation)
- **Haptic Feedback:** Use Telegram WebApp haptic API for important actions

## Telegram Mini App Specific
- **Theme Colors:** Use Telegram theme API for header/background
- **Back Button:** Handle Telegram back button properly
- **Main Button:** Use for checkout and primary actions
- **Haptics:** Light feedback on add to cart, medium on errors

## Responsive Breakpoints
- **Mobile:** 320px - 420px (primary focus)
- **Small phones:** 320px - 375px
- **Medium phones:** 375px - 414px
- **Large phones:** 414px - 420px

## Do's
✅ Use simple, flat design  
✅ Optimize for touch  
✅ Load images lazily  
✅ Use Telegram WebApp API  
✅ Keep it minimal and fast  
✅ Follow color scheme from config

## Don'ts
❌ No hover effects  
❌ No complex animations  
❌ No desktop layouts  
❌ No tiny touch targets  
❌ No heavy images  
❌ No hardcoded colors (use config)
