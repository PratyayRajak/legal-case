# Production Deployment & Operations Guide

This guide covers production deployment options, system configuration, database initialization, security considerations, and routine operations for the Court Brief Engine.

---

## 1. Quickstart: Production with Docker Compose

To deploy the entire production stack (FastAPI backend, Next.js frontend, PostgreSQL, Redis, MinIO) on a single Ubuntu / Debian server:

```bash
# 1. Clone repository
git clone https://github.com/organization/court-brief-engine.git
cd court-brief-engine

# 2. Configure production environment
cp .env.production.example .env.production
# Generate secure keys:
# openssl rand -hex 32
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
nano .env.production

# 3. Launch with Docker Compose
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verify service health
docker compose -f docker-compose.prod.yml ps
curl http://localhost:8000/health
curl -I http://localhost:3000
```

---

## 2. Reverse Proxy & SSL (Nginx / Caddy)

For public production access, place an SSL-terminating reverse proxy in front of the services.

### Example Nginx Configuration (`/etc/nginx/sites-available/court-brief.conf`)

```nginx
server {
    listen 80;
    server_name court.yourdomain.gov.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name court.yourdomain.gov.in;

    ssl_certificate /etc/letsencrypt/live/court.yourdomain.gov.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/court.yourdomain.gov.in/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Maximum PDF upload size
    client_max_body_size 50M;

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Legal-Disclaimer "AI-assisted summary. Verify against the source document." always;

    # Next.js Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # FastAPI Backend APIs
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

---

## 3. Database Initialization & Migrations

The database models are managed via SQLAlchemy 2.0 and Alembic.

```bash
# Run database migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Seed initial court rules
docker compose -f docker-compose.prod.yml exec backend python scripts/import_rules.py --import data/rules/up_revenue_code_rules.csv
```

---

## 4. Backups & Disaster Recovery

### Database Daily Backup (Cron)
```bash
# Add to crontab: 0 2 * * * /opt/scripts/backup-court-db.sh
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U courtuser courtdb | gzip > /opt/backups/courtdb_$TIMESTAMP.sql.gz
# Retain 30 days locally
find /opt/backups/ -type f -name "courtdb_*.sql.gz" -mtime +30 -delete
```

### Document Storage (MinIO / S3)
Set up automated S3 cross-region replication or daily snapshots with AWS S3 Lifecycle policies.

---

## 5. Security & Legal Compliance Checklist

- [x] **DPDPA 2023 Compliance**: Litigant PII encrypted with reversible Fernet keys before external storage.
- [x] **Data Residency**: Deployed strictly within Indian territory (AWS `ap-south-1` Mumbai).
- [x] **Mandatory Disclaimer**: Disclaimers enforced at HTTP response header level, API payload level, and UI view layer.
- [x] **Immutable Audit Trail**: SHA-256 document hashing and user action tracking in audit service.
- [x] **Zero LLM Hallucination in Rule Checks**: Legal compliance is determined strictly by the Python deterministic rules engine, never by LLM output.
