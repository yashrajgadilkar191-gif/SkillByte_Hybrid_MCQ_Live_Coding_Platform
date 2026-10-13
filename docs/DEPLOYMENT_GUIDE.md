# SKILLBYTE — Production Deployment & Operations Guide

> **Document ID**: `DELIV-06`  
> **Classification**: Production Operations & Deployment Runbook  
> **Release Target**: SkillByte v1.0.0 (`v1.0.0-final-release`)  
> **Target OS**: Linux (Ubuntu 22.04 LTS) / Containerized Stack  

---

## 1. Production Architecture Overview

In a production environment, SkillByte is deployed using an industry-standard reverse proxy and WSGI worker topology:

```
[Clients / Web Browsers]
           │ HTTPS (Port 443)
           ▼
[Nginx Reverse Proxy & SSL Termination]
     │                                    │
     │ /static/ (Direct Disk Serve)       │ Proxy Pass (HTTP / Socket)
     ▼                                    ▼
[Static Files Cache]              [Gunicorn WSGI Application Server]
(/var/www/skillbyte/staticfiles)  (4-8 Worker Processes on :8000)
                                          │
                                          │ Django ORM (Port 5432)
                                          ▼
                                  [PostgreSQL 15 Database]
                                  (skillbyte_db)
                                          │
                                          │ Internal REST (Port 2358)
                                          ▼
                                  [Self-Hosted Judge0 Engine]
                                  (Redis Broker + Docker Workers)
```

---

## 2. Hardware Sizing & System Prerequisites

### 2.1 Recommended Hardware Sizing
- **Operating System**: Ubuntu 22.04 LTS (x86_64) with Linux Kernel 5.15+ (cgroups v2 support).
- **vCPU**: Minimum 2 vCPUs (Recommended: 4 vCPUs for concurrent code compilation).
- **RAM**: Minimum 4 GB (Recommended: 8 GB to support concurrent Judge0 Docker execution).
- **Storage**: 25 GB+ SSD (supporting Docker images for Python, OpenJDK, and GCC).

### 2.2 Software Dependencies
```bash
# Update system repositories
sudo apt update && sudo apt upgrade -y

# Install Core Runtimes & Build Tools
sudo apt install -y python3.10 python3.10-venv python3-pip python3-dev \
    postgresql postgresql-contrib libpq-dev \
    nginx curl git build-essential certbot python3-certbot-nginx

# Install Docker & Docker Compose Plugin
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

---

## 3. PostgreSQL Database Provisioning

Log in to the PostgreSQL administrative console to create the dedicated user and database:

```bash
sudo -u postgres psql
```

Execute the following SQL commands:
```sql
-- Create dedicated database user
CREATE USER skillbyte_user WITH PASSWORD 'StrongProductionPasswordHere123!';

-- Set optimal character encoding and transaction parameters
ALTER ROLE skillbyte_user SET client_encoding TO 'utf8';
ALTER ROLE skillbyte_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE skillbyte_user SET timezone TO 'UTC';

-- Create production database
CREATE DATABASE skillbyte_db OWNER skillbyte_user;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE skillbyte_db TO skillbyte_user;

\q
```

---

## 4. Self-Hosted Judge0 Docker Stack Setup

Deploy Judge0 on port `2358` using its official Docker Compose deployment:

```bash
# Create directory for Judge0
mkdir -p /opt/judge0 && cd /opt/judge0

# Download Judge0 official docker-compose and configuration files
curl -fsSL https://raw.githubusercontent.com/judge0/judge0/master/docker-compose.yml -o docker-compose.yml
curl -fsSL https://raw.githubusercontent.com/judge0/judge0/master/judge0.conf -o judge0.conf

# Start Judge0 in background
docker compose up -d

# Verify health status
curl http://localhost:2358/system_info
```

---

## 5. Application Setup & Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-org/skillbyte.git /var/www/skillbyte
cd /var/www/skillbyte

# Create Python virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install Python production dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

---

## 6. Environment Configuration (`.env.production`)

Create `/var/www/skillbyte/.env`:
```ini
# Production Django Settings
SECRET_KEY=generate-a-cryptographically-secure-50-character-key-here
DEBUG=False
ALLOWED_HOSTS=skillbyte.example.com,www.skillbyte.example.com,127.0.0.1,localhost

# PostgreSQL Database Configuration
DB_NAME=skillbyte_db
DB_USER=skillbyte_user
DB_PASSWORD=StrongProductionPasswordHere123!
DB_HOST=127.0.0.1
DB_PORT=5432

# Judge0 Sandboxed Execution Service
JUDGE0_URL=http://127.0.0.1:2358

# JWT Expiration Parameters
JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=7
```

---

## 7. Database Migrations & Static File Collection

```bash
cd /var/www/skillbyte/backend
source /var/www/skillbyte/venv/bin/activate

# Apply PostgreSQL database migrations
python manage.py migrate

# Create the initial administrator superuser
python manage.py createsuperuser

# Collect all static files (CSS, JS, Monaco, Icons) into STATIC_ROOT
python manage.py collectstatic --noinput
```

---

## 8. Gunicorn Systemd Service Configuration

Create a systemd unit file at `/etc/systemd/system/skillbyte.service`:

```ini
[Unit]
Description=Gunicorn daemon for SKILLBYTE Hybrid Assessment Platform
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/skillbyte/backend
EnvironmentFile=/var/www/skillbyte/.env
ExecStart=/var/www/skillbyte/venv/bin/gunicorn \
          --access-logfile /var/log/skillbyte/access.log \
          --error-logfile /var/log/skillbyte/error.log \
          --workers 5 \
          --worker-class gthread \
          --threads 2 \
          --timeout 60 \
          --bind 127.0.0.1:8000 \
          config.wsgi:application

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the Gunicorn service:
```bash
# Create log directory and set permissions
sudo mkdir -p /var/log/skillbyte
sudo chown -R www-data:www-data /var/log/skillbyte
sudo chown -R www-data:www-data /var/www/skillbyte

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl start skillbyte
sudo systemctl enable skillbyte
sudo systemctl status skillbyte
```

---

## 9. Nginx Reverse Proxy & SSL Configuration

Create the Nginx server block at `/etc/nginx/sites-available/skillbyte`:

```nginx
# Upstream Gunicorn Cluster
upstream skillbyte_cluster {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name skillbyte.example.com www.skillbyte.example.com;

    # Maximum upload size (for code submissions)
    client_max_body_size 10M;

    # Serve static assets directly from disk
    location /static/ {
        alias /var/www/skillbyte/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
    }

    # Proxy all application requests to Gunicorn
    location / {
        proxy_pass http://skillbyte_cluster;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable configuration and issue SSL certificates via Let's Encrypt:
```bash
sudo ln -s /etc/nginx/sites-available/skillbyte /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# Install free trusted SSL certificate
sudo certbot --nginx -d skillbyte.example.com -d www.skillbyte.example.com
```

---

## 10. Development vs. Production Configuration Comparison

| Configuration Property | Development (Current) | Production (Deployment Guide) |
|---|---|---|
| **OS Environment** | Windows 10/11 | Ubuntu 22.04 LTS Linux |
| **WSGI Server** | Django `runserver` (single threaded) | Gunicorn (5 workers, multi-threaded) |
| **Reverse Proxy** | Direct port connection (`127.0.0.1:8000`) | Nginx with SSL termination (Port 443) |
| **Static File Delivery** | Django static view handler | Nginx direct filesystem cache (`expires 30d`) |
| **DEBUG Flag** | `DEBUG = True` | `DEBUG = False` |
| **Secret Key** | Development fallback string | Cryptographically random 50-char token |
| **Database Engine** | PostgreSQL (`localhost:5432`) | PostgreSQL with connection pooling |
| **SSL / HTTPS** | Plaintext HTTP | Enforced TLS 1.3 via Let's Encrypt |

---

## 11. Maintenance, Backups & Health Monitoring

### 11.1 Automated PostgreSQL Backup Script
Create `/usr/local/bin/backup_skillbyte.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/skillbyte"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p $BACKUP_DIR

# Generate compressed database dump
PGPASSWORD="StrongProductionPasswordHere123!" pg_dump -U skillbyte_user -h 127.0.0.1 skillbyte_db | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# Delete backups older than 14 days
find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +14 -delete
```
Schedule via cron (`crontab -e`):
```cron
0 2 * * * /usr/local/bin/backup_skillbyte.sh
```

### 11.2 Production Health Verification Commands
```bash
# Check Django service status
sudo systemctl status skillbyte

# Check Nginx status
sudo systemctl status nginx

# Verify API health check endpoint
curl -s http://127.0.0.1:8000/api/health/ | jq .

# Monitor real-time logs
sudo journalctl -u skillbyte -f
```

