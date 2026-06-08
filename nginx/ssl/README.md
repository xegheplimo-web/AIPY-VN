# SSL Certificates

This directory is where nginx looks for SSL/TLS certificates.

## Required Files

For production HTTPS, place the following files here:

| File | Description |
|------|-------------|
| `fullchain.pem` | Full certificate chain (server cert + intermediate certs) |
| `privkey.pem` | Private key for the server certificate |

## Using Let's Encrypt (certbot)

```bash
# Install certbot
apt-get install certbot

# Obtain a certificate (stop nginx first)
certbot certonly --standalone -d your-domain.com

# Copy certificates
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./nginx/ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./nginx/ssl/

# Set permissions
chmod 600 ./nginx/ssl/privkey.pem
chmod 644 ./nginx/ssl/fullchain.pem
```

## Auto-Renewal with certbot

```bash
# Add to crontab for automatic renewal
0 0 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/*.pem /path/to/AIPY-VN/nginx/ssl/ && docker-compose -f docker-compose.prod.yml restart nginx
```

## Using Custom Certificates

1. Place your `fullchain.pem` and `privkey.pem` in this directory.
2. Ensure the private key has restricted permissions:
   ```bash
   chmod 600 privkey.pem
   ```
3. The nginx production config (`nginx.prod.conf`) references these files at `/etc/nginx/ssl/`.

## Development

For local development, SSL is not required. The dev `nginx.conf` does not enable HTTPS by default. The SSL volume mount in `docker-compose.yml` will mount this directory, but nginx will simply ignore it if no HTTPS server block is active.

**Never commit actual certificate or key files to version control.** Add `*.pem` to `.gitignore`.
