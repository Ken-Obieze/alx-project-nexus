# PollR Deployment Guide

This document covers the complete CI/CD pipeline and deployment process for PollR.

## 🚀 CI/CD Pipeline Overview

### GitHub Actions Workflow

The CI/CD pipeline (`/.github/workflows/ci-cd.yml`) includes:

#### **Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Release publications

#### **Jobs:**

1. **Test Job** (`ubuntu-latest`)
   - Python 3.11 setup
   - Code quality checks (Black, isort, Flake8)
   - Django system checks
   - Database migrations
   - Unit tests with pytest and coverage
   - GraphQL schema testing

2. **Security Job** (`ubuntu-latest`)
   - Dependency vulnerability scanning (Safety)
   - Code security analysis (Bandit)

3. **Build Job** (on releases)
   - Python package building
   - Artifact storage

4. **Docker Job** (on releases)
   - Multi-platform Docker builds (amd64, arm64)
   - Docker Hub publishing

5. **Deploy Jobs**
   - Staging deployment (develop branch)
   - Production deployment (releases)

## 🐳 Docker Configuration

### Development Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services included:
- **PostgreSQL** (port 5432)
- **Redis** (port 6379)
- **Django Web App** (port 8000)
- **Celery Worker**
- **Celery Beat Scheduler**

### Production Docker Compose

```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

Additional services:
- **Nginx** reverse proxy (ports 80, 443)

## 🔧 Environment Variables

### Required for Production

Create `.env` file with:

```env
# Database
DATABASE_NAME=pollrdb
DATABASE_USER=postgres
DATABASE_PASSWORD=your-secure-password
DATABASE_HOST=db
DATABASE_PORT=5432

# Django
SECRET_KEY=your-super-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Redis/Celery
REDIS_CLOUD_HOST=redis
REDIS_CLOUD_PORT=6379
REDIS_CLOUD_SSL=False
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@pollr.com
```

## 📦 Deployment Options

### Option 1: Docker (Recommended)

1. **Build Image:**
   ```bash
   docker build -t pollr-backend .
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

### Option 2: Traditional Deployment

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables:**
   ```bash
   export DATABASE_NAME=pollrdb
   export SECRET_KEY=your-secret-key
   # ... other variables
   ```

3. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Collect Static Files:**
   ```bash
   python manage.py collectstatic --noinput
   ```

5. **Start Services:**
   ```bash
   # Web server
   gunicorn pollr_backend.wsgi:application
   
   # Celery worker
   celery -A pollr_backend.background_tasks worker --loglevel=info
   
   # Celery beat
   celery -A pollr_backend.background_tasks beat --loglevel=info
   ```

## 🔍 Health Checks

### Application Health Endpoints

- **Health Check:** `GET /health/`
- **API Status:** `GET /`
- **GraphQL:** `POST /graphql/`

### Docker Health Checks

```bash
# Check container health
docker ps

# View health logs
docker inspect <container_name>
```

## 🚨 Monitoring

### Application Monitoring

1. **Django Logs:**
   - Application logs in `/app/logs/`
   - Celery task logs

2. **Database Monitoring:**
   - PostgreSQL connection pool
   - Query performance

3. **Redis Monitoring:**
   - Memory usage
   - Connection count

### Infrastructure Monitoring

1. **Container Monitoring:**
   ```bash
   docker stats
   ```

2. **Log Aggregation:**
   ```bash
   docker-compose logs -f
   ```

## 🔐 Security Considerations

### Production Security

1. **Environment Variables:**
   - Never commit secrets to Git
   - Use GitHub Secrets or environment-specific files

2. **Database Security:**
   - Strong passwords
   - SSL connections
   - Regular backups

3. **Web Security:**
   - HTTPS enforcement
   - CSRF protection
   - Security headers

4. **Docker Security:**
   - Non-root user
   - Minimal base images
   - Regular security updates

## 🔄 Release Process

### Git Flow Workflow

1. **Start Release:**
   ```bash
   git flow release start 1.0.0
   ```

2. **Finish Release:**
   ```bash
   git flow release finish 1.0.0
   ```

3. **Push to Remote:**
   ```bash
   git push origin main
   git push origin develop
   git push --tags
   ```

### Automated Release Process

1. **Create GitHub Release:**
   - Tag version (e.g., `v1.0.0`)
   - Add release notes

2. **CI/CD Pipeline:**
   - Runs tests automatically
   - Builds Docker image
   - Deploys to production

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection:**
   ```bash
   # Check PostgreSQL
   docker-compose exec db pg_isready
   
   # Check logs
   docker-compose logs db
   ```

2. **Redis Connection:**
   ```bash
   # Check Redis
   docker-compose exec redis redis-cli ping
   
   # Check logs
   docker-compose logs redis
   ```

3. **Celery Issues:**
   ```bash
   # Check worker status
   docker-compose exec celery celery -A pollr_backend.background_tasks inspect active
   
   # Check logs
   docker-compose logs celery
   ```

4. **Django Issues:**
   ```bash
   # Run Django checks
   docker-compose exec web python manage.py check --deploy
   
   # Check migrations
   docker-compose exec web python manage.py showmigrations
   ```

## 📊 Performance Optimization

### Database Optimization

1. **Indexing:**
   - Add database indexes for frequently queried fields
   - Monitor slow queries

2. **Connection Pooling:**
   - Configure connection pool limits
   - Monitor connection usage

### Application Optimization

1. **Caching:**
   - Redis caching for frequently accessed data
   - Django cache framework

2. **Static Files:**
   - CDN for static assets
   - Compressed assets

## 🔄 Backup Strategy

### Database Backups

```bash
# Create backup
docker-compose exec db pg_dump -U postgres pollrdb > backup.sql

# Restore backup
docker-compose exec -T db psql -U postgres pollrdb < backup.sql
```

### Automated Backups

Set up cron jobs or use database backup services for regular backups.

## 📞 Support

For deployment issues:

1. Check the logs
2. Verify environment variables
3. Test database connections
4. Review CI/CD pipeline logs
5. Check GitHub Actions status

---

**Note:** This deployment guide assumes you have Docker and Docker Compose installed. For traditional deployments, adjust the instructions accordingly.
