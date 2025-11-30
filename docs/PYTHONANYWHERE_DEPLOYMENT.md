# PollR PythonAnywhere Deployment Guide

This guide will help you deploy your PollR application to PythonAnywhere.

## 🚀 Prerequisites

1. **PythonAnywhere Account** (Free or Paid)
2. **GitHub Repository** with your code
3. **Redis Cloud Account** (for background tasks)
4. **Database** (PostgreSQL recommended)

## 📋 Step-by-Step Deployment

### 1. Setup PythonAnywhere Account

1. **Sign up** at [pythonanywhere.com](https://www.pythonanywhere.com/)
2. **Choose a plan** (Free for testing, Paid for production)
3. **Note your username** (e.g., `yourusername`)

### 2. Create Web App

1. Go to **Web** tab in PythonAnywhere dashboard
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"**
4. Select **Python 3.11**
5. Set domain to your username (e.g., `yourusername.pythonanywhere.com`)

### 3. Clone Your Repository

```bash
# In PythonAnywhere Bash console
cd ~
git clone https://github.com/Ken-Obieze/alx-project-nexus.git
cd alx-project-nexus/pollr_backend
```

### 4. Setup Virtual Environment

```bash
# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.11 pollr_backend

# Activate it (should happen automatically)
workon pollr_backend

# Install dependencies
pip install -r requirements-prod.txt
```

### 5. Configure Environment Variables

Create `.env` file in your project directory:

```bash
nano .env
```

Add the following content:

```env
# Database (use PythonAnywhere PostgreSQL)
DATABASE_NAME=yourusername$pollrdb
DATABASE_USER=yourusername
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=yourusername.postgres.database.azure.com
DATABASE_PORT=5432

# Django
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourusername.pythonanywhere.com,www.yourusername.pythonanywhere.com

# Redis Cloud (for Celery)
REDIS_CLOUD_HOST=your-redis-cloud-host
REDIS_CLOUD_PORT=12345
REDIS_CLOUD_PASSWORD=your-redis-password
REDIS_CLOUD_SSL=True
CELERY_BROKER_URL=rediss://:your-redis-password@your-redis-host:12345/0
CELERY_RESULT_BACKEND=rediss://:your-redis-password@your-redis-host:12345/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@pollr.com
```

### 6. Setup Database

#### Option A: Use PythonAnywhere PostgreSQL (Recommended)

1. Go to **Databases** tab
2. Click **"Initialize a new PostgreSQL database"**
3. Note the connection details
4. Update `.env` file with the database info

#### Option B: Use External Database

1. Create PostgreSQL database elsewhere
2. Update `.env` with connection details

### 7. Run Migrations

```bash
python manage.py migrate
```

### 8. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 9. Configure WSGI File

1. Go to **Web** tab
2. Click **"WSGI configuration file"** link
3. Replace the content with:

```python
import os
import sys

# Add your project directory to the Python path
path = '/home/yourusername/alx-project-nexus/pollr_backend'
if path not in sys.path:
    sys.path.append(path)

# Set the DJANGO_SETTINGS_MODULE
os.environ['DJANGO_SETTINGS_MODULE'] = 'pollr_backend.settings'

# Import your Django application
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
from django.conf import settings

# Get the WSGI application
application = get_wsgi_application()

# Add WhiteNoise for static files
application = WhiteNoise(application, root=settings.STATIC_ROOT)
application.add_files(settings.STATIC_ROOT)
```

**Important**: Replace `yourusername` with your actual PythonAnywhere username.

### 10. Configure Web App

1. In **Web** tab, set:
   - **Code directory**: `/home/yourusername/alx-project-nexus/pollr_backend`
   - **Working directory**: `/home/yourusername/alx-project-nexus/pollr_backend`
   - **WSGI file**: `/var/www/yourusername_pythonanywhere_com_wsgi.py`

2. Set **Static files**:
   - **URL**: `/static/`
   - **Directory**: `/home/yourusername/alx-project-nexus/pollr_backend/staticfiles/`

### 11. Setup Celery (Background Tasks)

#### Create Celery Worker Script

Create `celery_worker.py`:

```python
#!/usr/bin/env python
import os
import sys
from celery import Celery

# Add project to path
sys.path.append('/home/yourusername/alx-project-nexus/pollr_backend')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pollr_backend.settings')

# Import and start Celery
from pollr_backend.background_tasks.celery import app

if __name__ == '__main__':
    app.start(['worker', '--loglevel=info'])
```

#### Create Celery Beat Script

Create `celery_beat.py`:

```python
#!/usr/bin/env python
import os
import sys

# Add project to path
sys.path.append('/home/yourusername/alx-project-nexus/pollr_backend')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pollr_backend.settings')

# Import and start Celery Beat
from pollr_backend.background_tasks.celery import app

if __name__ == '__main__':
    app.start(['beat', '--loglevel=info'])
```

#### Setup Scheduled Tasks

1. Go to **Tasks** tab in PythonAnywhere
2. **Add scheduled task** for Celery worker:
   - **Command**: `/home/yourusername/.virtualenvs/pollr_backend/bin/python /home/yourusername/alx-project-nexus/pollr_backend/celery_worker.py`
   - **Schedule**: **Always on (24/7)**
   - **Description**: "Celery Worker"

3. **Add scheduled task** for Celery beat:
   - **Command**: `/home/yourusername/alx-project-nexus/pollr_backend/celery_beat.py`
   - **Schedule**: **Always on (24/7)**
   - **Description**: "Celery Beat"

### 12. Reload Web App

1. Go to **Web** tab
2. Click **"Reload"** button
3. Wait for the reload to complete

### 13. Test Your Application

1. **Visit your domain**: `https://yourusername.pythonanywhere.com/`
2. **Check health endpoint**: `https://yourusername.pythonanywhere.com/health/`
3. **Test GraphQL**: `https://yourusername.pythonanywhere.com/graphql/`
4. **Check admin**: `https://yourusername.pythonanywhere.com/admin/`

## 🔧 Troubleshooting

### Common Issues

#### 1. 500 Internal Server Error

**Check logs**:
```bash
tail -f /var/log/yourusername.pythonanywhere.com.error.log
```

**Common fixes**:
- Check `.env` file permissions
- Verify database connection
- Check static files collection

#### 2. Database Connection Error

**Check database details**:
```bash
python manage.py check --database default
```

**Verify PostgreSQL**:
- Ensure database is created
- Check connection string format
- Verify credentials

#### 3. Static Files Not Loading

**Collect static files**:
```bash
python manage.py collectstatic --noinput --clear
```

**Check static files path**:
- Ensure `/staticfiles/` directory exists
- Check web app static files configuration

#### 4. Celery Not Working

**Check Celery logs**:
```bash
# In Tasks tab, check the task logs
```

**Test Celery manually**:
```bash
workon pollr_backend
cd ~/alx-project-nexus/pollr_backend
celery -A pollr_backend.background_tasks worker --loglevel=info
```

## 📊 Monitoring

### Application Logs

```bash
# Web app logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log
tail -f /var/log/yourusername.pythonanywhere.com.access.log

# Django logs
tail -f ~/alx-project-nexus/pollr_backend/django.log
```

### Database Monitoring

```bash
# Check database connections
python manage.py dbshell
```

### Celery Monitoring

```bash
# Check active tasks
celery -A pollr_backend.background_tasks inspect active
```

## 🚀 Performance Optimization

### Free Account Limitations

- **CPU time**: Limited to 1 CPU-hour per day
- **Memory**: 512MB RAM
- **Storage**: 1GB
- **Bandwidth**: Limited

### Optimization Tips

1. **Use caching** with Redis
2. **Optimize database queries**
3. **Compress static files**
4. **Use CDN for static assets**
5. **Monitor resource usage**

## 🔐 Security

### Security Checklist

- ✅ Set `DEBUG=False` in production
- ✅ Use strong `SECRET_KEY`
- ✅ Configure `ALLOWED_HOSTS`
- ✅ Use HTTPS (PythonAnywhere provides this)
- ✅ Secure database credentials
- ✅ Use environment variables for secrets

### Additional Security

1. **Enable HTTPS** (automatic on PythonAnywhere)
2. **Use strong passwords**
3. **Regular updates**
4. **Monitor access logs**

## 📈 Scaling

### Upgrade to Paid Plan

When you need more resources:
- **Hacker Plan**: $5/month - More CPU, memory, storage
- **Web Developer Plan**: $12/month - Even more resources
- **Custom Plans**: For large applications

### Scaling Strategies

1. **Database optimization**
2. **Caching implementation**
3. **Load balancing**
4. **CDN integration**

## 🔄 Updates and Maintenance

### Updating Your Application

```bash
cd ~/alx-project-nexus/pollr_backend
git pull origin main
workon pollr_backend
pip install -r requirements-prod.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

### Regular Maintenance

1. **Backup database** regularly
2. **Update dependencies**
3. **Monitor logs**
4. **Check resource usage**

## 📞 Support

### PythonAnywhere Support

- **Documentation**: [help.pythonanywhere.com](https://help.pythonanywhere.com/)
- **Forums**: Active community support
- **Email**: Support for paid accounts

### Django Support

- **Django Documentation**: [docs.djangoproject.com](https://docs.djangoproject.com/)
- **Stack Overflow**: Active Django community

---

**Note**: This guide assumes you're using PostgreSQL. If you're using SQLite or another database, adjust the configuration accordingly.
