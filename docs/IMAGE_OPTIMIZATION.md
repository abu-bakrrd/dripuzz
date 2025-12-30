# Image Optimization Guide

## Overview

Google Lighthouse recommends optimizing images to improve page load performance. This guide explains how to optimize product images for the MiniTaskerBot3 e-commerce platform.

## Recommended Image Specifications

### Product Images

- **Format**: WebP (preferred) or JPEG
- **Quality**: 85% compression for JPEG
- **Dimensions**:
  - Thumbnail: 400x400px
  - Detail view: 800x800px
  - High-res: 1200x1200px (optional)
- **File size**: < 100KB per image (thumbnail), < 200KB (detail)

### Logo & Static Assets

- **Format**: SVG (preferred) or PNG
- **Dimensions**: Actual display size (e.g., 32x32px for header logo)

## Optimization Tools

### Online Tools

1. **TinyPNG** (https://tinypng.com/) - PNG/JPEG compression
2. **Squoosh** (https://squoosh.app/) - WebP conversion and optimization
3. **ImageOptim** (https://imageoptim.com/) - Batch optimization (Mac)

### Command Line Tools

#### Using ImageMagick

```bash
# Convert to WebP with 85% quality
magick input.jpg -quality 85 output.webp

# Resize and optimize JPEG
magick input.jpg -resize 800x800 -quality 85 output.jpg

# Batch convert all JPEGs in a folder
for file in *.jpg; do magick "$file" -quality 85 "optimized_$file"; done
```

#### Using cwebp (WebP encoder)

```bash
# Convert JPEG to WebP
cwebp -q 85 input.jpg -o output.webp

# Batch convert
for file in *.jpg; do cwebp -q 85 "$file" -o "${file%.jpg}.webp"; done
```

## Implementation Steps

### 1. Optimize Existing Images

1. Download all product images from `/public/products/` or database
2. Run optimization tool (e.g., Squoosh, ImageMagick)
3. Replace original images with optimized versions
4. Verify image quality visually

### 2. Set Up Upload Pipeline

For future uploads, add image optimization to the admin panel:

- Install `sharp` library: `npm install sharp`
- Add server-side image processing in `/server/routes.ts`
- Automatically resize and compress on upload

### 3. Use Modern Formats

Update `ProductCard.tsx` and `ProductDetail.tsx` to use `<picture>` element:

```tsx
<picture>
	<source srcset='image.webp' type='image/webp' />
	<source srcset='image.jpg' type='image/jpeg' />
	<img src='image.jpg' alt='Product' loading='lazy' />
</picture>
```

## Performance Impact

Optimizing images can:

- Reduce page size by 50-70%
- Improve LCP (Largest Contentful Paint) by 1-2 seconds
- Save bandwidth costs
- Improve mobile experience

## Checklist

- [ ] Audit all product images for size and format
- [ ] Convert large images (>200KB) to WebP
- [ ] Compress JPEGs to 85% quality
- [ ] Resize images to appropriate dimensions
- [ ] Update image upload pipeline for automatic optimization
- [ ] Test image quality on various devices
- [ ] Re-run Lighthouse to verify improvements

## Notes

- Always keep original high-resolution images as backups
- Test image quality on retina displays
- Consider using a CDN with automatic image optimization (e.g., Cloudinary, imgix)
