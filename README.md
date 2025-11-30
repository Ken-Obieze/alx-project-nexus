# **PollR - Online Polling System Backend**

A robust, scalable online polling and election management system built with Django, featuring REST APIs, GraphQL, background tasks, and modern deployment capabilities.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/django-5.2.8-green.svg)
![PostgreSQL](https://img.shields.io/badge/postgreSQL-15+-blue.svg)

---

## 🚀 **Project Overview**

PollR is a comprehensive polling system that enables organizations to create, manage, and conduct secure elections with real-time results. The system supports:

- **🗳️ Election Management** - Create polls with multiple positions and candidates
- **👥 User & Organization Workflow** - Multi-tenant architecture with role-based access
- **🔒 Secure Voting** - One-vote-per-position enforcement with anonymous vote storage
- **📊 Real-Time Results** - Efficient result computation and analytics
- **🔄 Background Tasks** - Email notifications, reminders, and scheduled jobs
- **🌐 GraphQL & REST APIs** - Dual API support for maximum flexibility
- **☁️ Cloud Ready** - Docker containerization and CI/CD pipeline

---

## 📚 **Documentation**

### **Core Documentation**
- 📖 **[Project Requirements Document (PRD)](docs/PRD.md)** - Complete project specifications and requirements
- 🏗️ **[Entity Relationship Diagram (ERD)](docs/erd.png)** - Database schema visualization
- 📊 **[View Interactive ERD](https://www.dbdiagram.io/d/Online-Polling-System-691a294a6735e111700fd364)** - Interactive database diagram

### **API Documentation**
- 🌐 **[GraphQL API Guide](docs/README_GRAPHQL.md)** - Complete GraphQL implementation and queries
- 📚 **[REST API Documentation](http://localhost:8000/api/docs/)** - Interactive Swagger/OpenAPI docs

### **Deployment Guides**
- 🐳 **[General Deployment Guide](docs/DEPLOYMENT.md)** - Docker, CI/CD, and production deployment
- ☁️ **[PythonAnywhere Deployment](docs/PYTHONANYWHERE_DEPLOYMENT.md)** - Step-by-step PythonAnywhere setup
- 🔴 **[Redis Cloud Setup](docs/REDIS_CLOUD_SETUP.md)** - Redis configuration for background tasks

---

## 🛠️ **Technology Stack**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Django 5.2.8 | Web framework |
| **API** | DRF + GraphQL | REST & GraphQL APIs |
| **Database** | PostgreSQL 15+ | Primary data storage |
| **Cache/Broker** | Redis Cloud | Caching & message broker |
| **Background Tasks** | Celery | Async task processing |
| **Authentication** | JWT | Token-based auth |
| **Documentation** | Swagger/OpenAPI | API docs |
| **Containerization** | Docker | Deployment |
| **CI/CD** | GitHub Actions | Automated pipeline |
| **Testing** | pytest | Unit & integration tests |

---

## ⚡ **Key Features**

### **🗳️ Election Management**
- Create polls with multiple positions and candidates
- Set start/end times with automatic status updates
- Add/remove candidates dynamically
- Organization-level configurations

### **👥 Multi-Tenant Architecture**
- User registration and authentication
- Organization creation and management
- Membership approval workflows
- Role-based permissions (Admin, Org Admin, Voter)

### **🔒 Secure Voting System**
- One-vote-per-position enforcement
- Anonymous vote storage
- Duplicate voting protection
- Audit trail for all votes

### **📊 Real-Time Analytics**
- Live result computation
- Vote counting and statistics
- Election status monitoring
- Export capabilities

### **🔄 Background Processing**
- Email notifications for election events
- Automated reminders for voters
- Scheduled task processing
- Result cleanup and maintenance

### **🌐 Dual API Support**
- **REST API** - Traditional RESTful endpoints
- **GraphQL API** - Flexible query interface
- **Interactive Documentation** - Swagger & GraphiQL
- **Token Authentication** - JWT-based security

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.11+
- PostgreSQL 15+
- Redis (for background tasks)
- Git

### **Installation**

```bash
# 1. Clone the repository
git clone https://github.com/Ken-Obieze/alx-project-nexus.git
cd alx-project-nexus/pollr_backend

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your database and Redis credentials

# 5. Apply database migrations
python manage.py migrate

# 6. Create superuser (optional)
python manage.py createsuperuser

# 7. Collect static files
python manage.py collectstatic --noinput

# 8. Run the development server
python manage.py runserver
```

### **Environment Variables**

Create a `.env` file with:

```env
# Database
DATABASE_NAME=pollrdb
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis Cloud (for Celery)
REDIS_CLOUD_HOST=your-redis-host
REDIS_CLOUD_PORT=12345
REDIS_CLOUD_PASSWORD=your-redis-password
REDIS_CLOUD_SSL=True

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## 🌐 **API Endpoints**

### **REST API**
- **Base URL**: `http://localhost:8000/api/v1/`
- **Documentation**: `http://localhost:8000/api/docs/`
- **Schema**: `http://localhost:8000/api/schema/`

### **GraphQL API**
- **Endpoint**: `http://localhost:8000/graphql/`
- **Playground**: `http://localhost:8000/graphql/` (GraphiQL interface)

### **Key Endpoints**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API status and endpoints |
| `/health/` | GET | Health check |
| `/graphql/` | POST | GraphQL queries |
| `/api/v1/elections/` | GET/POST | Election management |
| `/api/v1/organizations/` | GET/POST | Organization management |
| `/api/v1/users/` | GET/POST | User management |
| `/api/v1/voting/` | GET/POST | Voting operations |

---

## 🧪 **Testing**

### **Run Test Suite**
```bash
# Run all tests
python manage.py test

# Run with coverage
pytest --cov=pollr_backend --cov-report=html

# Run specific app tests
python manage.py test elections
python manage.py test voting
```

### **Code Quality**
```bash
# Code formatting
black .

# Import sorting
isort .

# Linting
flake8 .

# Security scanning
bandit -r pollr_backend/
```

---

## 🔄 **Background Tasks (Celery)**

### **Start Celery Worker**
```bash
# Development
python start_celery_windows.py  # Windows
celery -A pollr_backend.background_tasks worker --loglevel=info  # Linux/Mac

# Production with Docker
docker-compose up celery
```

### **Start Celery Beat Scheduler**
```bash
# Development
python start_celery_windows.py beat

# Production with Docker
docker-compose up celery-beat
```

### **Available Tasks**
- `update_election_statuses` - Updates election statuses (every 5 minutes)
- `send_election_reminders` - Sends voting reminders (daily at 9 AM)
- `cleanup_old_votes` - Cleans up old vote data (monthly)

---

## 🐳 **Docker Deployment**

### **Development**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### **Production**
```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🚀 **CI/CD Pipeline**

The project includes a comprehensive CI/CD pipeline with:

- **✅ Code Quality** - Black, Flake8, isort checks
- **🧪 Testing** - pytest with coverage reporting
- **🔒 Security** - Bandit and Safety scanning
- **🐳 Docker** - Automated image building and pushing
- **📊 Coverage** - Codecov integration

**Trigger**: Push to `main` or `develop` branches

---

## 📱 **PythonAnywhere Deployment**

For easy deployment without Docker:

1. **Follow the [PythonAnywhere Deployment Guide](docs/PYTHONANYWHERE_DEPLOYMENT.md)**
2. **Setup Redis Cloud** using the [Redis Cloud Setup Guide](docs/REDIS_CLOUD_SETUP.md)
3. **Configure environment variables** for production
4. **Deploy** with automated scripts

---

## 🏗️ **System Architecture**

### **Database Design**
- **3NF Normalized** schema for data integrity
- **Optimized indexes** for fast queries
- **Foreign key constraints** for data consistency
- **Audit trails** for vote tracking

### **Security Features**
- **JWT Authentication** for API access
- **Role-based permissions** for different user types
- **Input validation** and sanitization
- **SQL injection prevention** through Django ORM
- **CORS configuration** for cross-origin requests

### **Performance Optimizations**
- **Database indexing** on frequently queried fields
- **Redis caching** for expensive operations
- **Background task processing** for async operations
- **Efficient query patterns** for result computation

---

## 🧠 **About the ProDev Backend Engineering Program**

This project was developed as part of the **ProDev Backend Engineering Program**, demonstrating mastery of modern backend development practices and real-world software engineering skills.

### **Major Learnings**

#### **Technical Skills**
- **Python & Django** - Advanced framework usage
- **Django REST Framework** - Professional API development
- **GraphQL** - Modern query language implementation
- **Docker & Containerization** - Production deployment
- **CI/CD (GitHub Actions)** - Automated development pipeline
- **Celery & Redis** - Background task processing
- **PostgreSQL** - Advanced database design
- **Testing** - Comprehensive test strategies

#### **Engineering Concepts**
- **Database Design & Normalization** - 3NF schema design
- **REST API Standards** - Best practices and conventions
- **Caching Strategies** - Performance optimization
- **Asynchronous Programming** - Background task handling
- **Authentication & Authorization** - Security implementation
- **System Design & Architecture** - Scalable system planning
- **Multi-tenant Architecture** - Organization isolation
- **API Documentation** - Professional documentation practices

---

## 🏆 **Challenges & Solutions**

### **1. Scalable Polling Database Design**
**Challenge**: Ensuring fast result computation under heavy voting loads.  
**Solution**:
- Normalized schema (3NF) with proper indexing
- Optimized query patterns for vote counting
- Database-level constraints for data integrity

### **2. Secure Voting Implementation**
**Challenge**: Enforcing one-vote-per-position while maintaining anonymity.  
**Solution**:
- Unique constraint enforcement at database level
- Anonymous vote storage with audit trails
- Atomic transactions for vote processing

### **3. Multi-tenant Architecture**
**Challenge**: Managing multiple organizations with data isolation.  
**Solution**:
- Organization-based data segregation
- Role-based permission system
- Custom middleware for tenant identification

### **4. Background Task Processing**
**Challenge**: Handling email notifications and scheduled tasks reliably.  
**Solution**:
- Celery with Redis Cloud for distributed task processing
- Error handling and retry mechanisms
- Monitoring and logging for task execution

---

## 🎯 **Personal Takeaways**

- **Scalable Architecture**: Deep understanding of building systems that grow
- **Database Mastery**: Advanced PostgreSQL design and optimization
- **API Excellence**: Professional REST and GraphQL API development
- **Modern DevOps**: CI/CD, containerization, and deployment automation
- **Security Best Practices**: Authentication, authorization, and data protection
- **Performance Engineering**: Caching, optimization, and monitoring
- **Documentation**: Comprehensive API and system documentation
- **Testing Strategies**: Unit, integration, and end-to-end testing

---

## 📄 **License**

This project is licensed under the [MIT License](LICENSE).

---

## 🤝 **Contributing**

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 **Support**

For questions or support:

- 📧 **Email**: [kenneth.obieze@outlook.com]
- 🐛 **Issues**: [GitHub Issues](https://github.com/Ken-Obieze/alx-project-nexus/issues)
- 📖 **Documentation**: See the [docs](docs/) folder for detailed guides

---

**Built with ❤️ for the ProDev Backend Engineering Program**