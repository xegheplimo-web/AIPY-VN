# CDN Integration Guide

This guide explains how to integrate a CDN (Content Delivery Network) with the VietStore frontend applications for improved performance and global content delivery.

## Supported CDNs

- **Cloudflare CDN** (Recommended)
- **AWS CloudFront**
- **Azure CDN**
- **Fastly**
- **Cloudinary** (for images)

## Setup Instructions

### 1. Build with CDN Configuration

```bash
# Use CDN-specific Vite config
cd apps/web-customer
cp vite.config.cdn.ts vite.config.ts
npm run build

cd ../web-owner
cp vite.config.cdn.ts vite.config.ts
npm run build

cd ../web-admin
cp vite.config.cdn.ts vite.config.ts
npm run build
```

### 2. Upload to CDN

#### Cloudflare CDN

```bash
# Install Wrangler CLI
npm install -g @cloudflare/wrangler

# Login to Cloudflare
wrangler login

# Upload static assets
wrangler pages deploy dist --project-name=vietstore-customer
wrangler pages deploy dist --project-name=vietstore-owner
wrangler pages deploy dist --project-name=vietstore-admin
```

#### AWS CloudFront

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Sync to S3 (origin)
aws s3 sync dist/ s3://vietstore-customer --acl public-read
aws s3 sync dist/ s3://vietstore-owner --acl public-read
aws s3 sync dist/ s3://vietstore-admin --acl public-read

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

### 3. Configure Environment Variables

Update `.env` files to use CDN URLs:

```env
# web-customer/.env
VITE_CDN_URL=https://cdn.vietstore.vn
VITE_API_URL=https://api.vietstore.vn

# web-owner/.env
VITE_CDN_URL=https://cdn-owner.vietstore.vn
VITE_API_URL=https://api.vietstore.vn

# web-admin/.env
VITE_CDN_URL=https://cdn-admin.vietstore.vn
VITE_API_URL=https://api.vietstore.vn
```

### 4. Update Asset Loading

In your React components, use CDN URLs for static assets:

```typescript
const getImageUrl = (path: string) => {
  const cdnUrl = import.meta.env.VITE_CDN_URL;
  return `${cdnUrl}/assets/${path}`;
};
```

## Image Optimization

For image optimization, use Cloudinary:

```typescript
import { Cloudinary } from '@cloudinary/url-gen';

const cloudinary = new Cloudinary({
  cloud: {
    cloudName: 'vietstore',
  },
});

const getOptimizedImageUrl = (publicId: string, width: number, height: number) => {
  return cloudinary
    .image(publicId)
    .format('auto')
    .quality('auto')
    .resize(width, height)
    .toURL();
};
```

## Cache Configuration

### CDN Cache Rules

- **HTML**: No cache (or 5 minutes)
- **CSS/JS**: 1 year with versioning
- **Images**: 1 year
- **API responses**: No cache (or 5 minutes)

### Browser Cache Headers

Configure your CDN to add appropriate cache headers:

```
Cache-Control: public, max-age=31536000, immutable
```

## Performance Benefits

- **Reduced Latency**: Content served from edge locations
- **Reduced Bandwidth**: Gzip compression and minification
- **Improved SEO**: Faster page load times
- **Global Reach**: Content available worldwide
- **DDoS Protection**: CDN provides DDoS mitigation

## Monitoring

Monitor CDN performance using:

- **Cloudflare Analytics**: Request count, bandwidth, cache hit ratio
- **AWS CloudWatch**: Requests, errors, latency
- **Grafana**: Custom metrics dashboard

## Rollback

If CDN deployment fails, revert to previous version:

```bash
# Cloudflare
wrangler pages rollback --project-name=vietstore-customer

# AWS CloudFront
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

## Cost Optimization

- Use CDN only for static assets
- Enable compression
- Set appropriate cache TTL
- Monitor bandwidth usage
- Use regional CDNs if needed
