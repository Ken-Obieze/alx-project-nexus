# Redis Cloud Setup Guide

This guide will help you configure Redis Cloud for your PollR application.

## Step 1: Get Redis Cloud Credentials

1. **Sign up for Redis Cloud** (if you haven't already):
   - Go to [Redis Cloud](https://redis.com/try-free/)
   - Create a free account or sign in

2. **Create a Redis Database**:
   - Click "Create Database" 
   - Choose "Redis" (not Redis Stack)
   - Select a plan (Free tier is sufficient for development)
   - Choose a cloud provider and region closest to you
   - Set database name (e.g., "pollr-redis")
   - Enable TLS/SSL (recommended for production)
   - Note the connection details

3. **Get Connection Details**:
   - From your database dashboard, click "Connect"
   - Copy the "Public endpoint" (host:port)
   - Copy the password
   - Note if TLS/SSL is enabled

## Step 2: Configure Environment Variables

Create or update your `.env` file in the project root:

```env
# Redis Cloud Configuration
REDIS_CLOUD_HOST=your-redis-cloud-host
REDIS_CLOUD_PORT=12345
REDIS_CLOUD_PASSWORD=your-redis-cloud-password
REDIS_CLOUD_SSL=true

# Celery (using Redis Cloud)
CELERY_BROKER_URL=redis://:your-redis-cloud-password@your-redis-cloud-host:12345/0
CELERY_RESULT_BACKEND=redis://:your-redis-cloud-password@your-redis-cloud-host:12345/0

# Other existing settings...
DATABASE_NAME=pollrdb
DATABASE_USER=postgres
DATABASE_PASSWORD=password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@pollr.com

# Django
SECRET_KEY=your-secret-key
DEBUG=True
```

**Important**: Replace the values with your actual Redis Cloud credentials.

## Step 3: Install Dependencies

```bash
pip install -r requirements_new.txt
```

This includes:
- `redis==5.0.1` - Redis Python client
- `redis-py-cluster==2.1.3` - Redis Cluster support
- `celery==5.3.6` - Celery task queue

## Step 4: Test Connection

Run the Redis Cloud connection test:

```bash
python manage.py test_redis_cloud
```

You should see output like:
```
Testing Redis Cloud connection...
Connecting to: your-redis-cloud-host:12345
✓ Redis Cloud connection successful
✓ Redis read/write test successful
✓ Celery broker connection successful
```

## Step 5: Start Services

Once the connection test passes, start your services:

### 5.1 Start Django Development Server
```bash
python manage.py runserver
```

### 5.2 Start Celery Worker
```bash
celery -A pollr_backend.background_tasks worker --loglevel=info
```

### 5.3 Start Celery Beat Scheduler
```bash
celery -A pollr_backend.background_tasks beat --loglevel=info
```

## Step 6: Verify Everything Works

1. **Test GraphQL API**:
   - Navigate to `http://localhost:8000/graphql/`
   - Try a simple query to verify the API works

2. **Test Background Tasks**:
   ```bash
   python manage.py shell
   >>> from background_tasks.tasks.elections_tasks import update_election_statuses
   >>> result = update_election_statuses.delay()
   >>> print(result.get())  # Should return task result
   ```

## Troubleshooting

### Common Issues and Solutions

#### 1. Connection Timeout
```
Error: redis.exceptions.ConnectionError: Timeout connecting to server
```
**Solution**:
- Check if the Redis Cloud endpoint is correct
- Verify your network allows outbound connections to Redis Cloud
- Check if Redis Cloud subscription is active

#### 2. Authentication Error
```
Error: redis.exceptions.AuthenticationError: WRONGPASS invalid username-password pair
```
**Solution**:
- Double-check the password in your `.env` file
- Ensure there are no extra spaces or special characters
- Try resetting the password in Redis Cloud console

#### 3. SSL/TLS Error
```
Error: redis.exceptions.ConnectionError: SSL handshake failed
```
**Solution**:
- Ensure `REDIS_CLOUD_SSL=true` if your Redis Cloud database has TLS enabled
- Check if your firewall blocks SSL connections
- Try with `REDIS_CLOUD_SSL=false` if you're not using TLS

#### 4. Import Error
```
ModuleNotFoundError: No module named 'redis'
```
**Solution**:
```bash
pip install redis redis-py-cluster
```

#### 5. Celery Connection Issues
```
Error: [Errno 111] Connection refused
```
**Solution**:
- Ensure Redis Cloud connection test passes first
- Check Celery configuration in settings.py
- Verify broker URL format is correct

### Debug Mode

For detailed debugging, you can enable Redis logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Considerations

1. **Use Environment Variables**: Never commit credentials to version control
2. **Enable SSL**: Always use TLS/SSL in production
3. **Monitor Usage**: Keep an eye on Redis Cloud memory usage
4. **Backup**: Redis Cloud includes automatic backups
5. **Scaling**: Consider upgrading your Redis Cloud plan as needed

## Example .env File

Here's a complete example `.env` file for reference:

```env
# Database
DATABASE_NAME=pollrdb
DATABASE_USER=postgres
DATABASE_PASSWORD=your_postgres_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis Cloud (replace with your actual values)
REDIS_CLOUD_HOST=redis-12345.c1.us-east-1-1.ec2.cloud.redislabs.com
REDIS_CLOUD_PORT=12345
REDIS_CLOUD_PASSWORD=your_redis_password_here
REDIS_CLOUD_SSL=true

# Celery URLs (auto-generated from above)
CELERY_BROKER_URL=redis://:your_redis_password_here@redis-12345.c1.us-east-1-1.ec2.cloud.redislabs.com:12345/0
CELERY_RESULT_BACKEND=redis://:your_redis_password_here@redis-12345.c1.us-east-1-1.ec2.cloud.redislabs.com:12345/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@pollr.com

# Django
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
```

## Next Steps

Once Redis Cloud is configured and working:

1. **Run migrations**: `python manage.py migrate`
2. **Create superuser**: `python manage.py createsuperuser`
3. **Test the full application**: Access `http://localhost:8000/graphql/`
4. **Monitor tasks**: Use Flower for Celery monitoring (optional)

Your PollR application is now ready with Redis Cloud as the message broker!
