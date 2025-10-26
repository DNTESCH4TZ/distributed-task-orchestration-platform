# 🚀 Getting Started Guide

> Quick guide to get Task Orchestrator Platform up and running

---

## Prerequisites

- **Python 3.11+** installed
- **Docker & Docker Compose** installed
- **Git** installed
- At least **4GB RAM** available

---

## Step-by-Step Setup

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd distributed-task-orchestration-platform
```

### 2. Setup Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env if needed (defaults work for local development)
```

### 3. Start Infrastructure

```bash
# Start all services (PostgreSQL, Redis, RabbitMQ, etc.)
make docker-up

# Check status
make docker-ps

# View logs
make docker-logs
```

Wait for all services to be healthy (~30 seconds).

### 4. Install Dependencies

**Option A: Using pip**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Option B: Using Poetry**
```bash
poetry install
poetry shell
```

### 5. Initialize Database

```bash
# Run migrations
make migrate

# Verify
python scripts/health_check.py
```

### 6. Start Application

```bash
# Development mode (hot reload)
make run

# Or manually
uvicorn src.main:app --reload
```

Application starts at `http://localhost:8000`

### 7. Start Celery Worker (Optional)

In a new terminal:

```bash
# Activate venv first
source venv/bin/activate

# Start worker
make run-worker
```

---

## Verify Installation

### 1. Check API Health

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T...",
  "version": "0.1.0",
  "environment": "development"
}
```

### 2. Open API Documentation

Visit: `http://localhost:8000/docs`

You should see the interactive Swagger UI.

### 3. Create Your First Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Workflow",
    "description": "A simple test workflow",
    "tasks": [
      {
        "name": "task_1",
        "type": "http",
        "payload": {
          "url": "https://httpbin.org/get",
          "method": "GET"
        }
      }
    ]
  }'
```

### 4. View Monitoring

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (admin/admin)
- **Jaeger:** http://localhost:16686
- **RabbitMQ:** http://localhost:15672 (guest/guest)

---

## Common Commands

```bash
# Development
make run              # Start API server
make run-worker       # Start Celery worker
make test             # Run tests
make format           # Format code
make lint             # Lint code

# Docker
make docker-up        # Start all services
make docker-down      # Stop all services
make docker-logs      # View logs

# Database
make migrate          # Apply migrations
make migrate-create msg="add users"  # Create migration

# Health
make health           # Check system health

# Documentation
make docs             # Build docs
make api-docs         # Open API docs
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in .env
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
make docker-ps

# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Redis Connection Failed

```bash
# Check Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis
```

### Migrations Failed

```bash
# Reset database (⚠️ destroys data)
make docker-down
make docker-up
make migrate
```

---

## Next Steps

1. **Read Documentation**
   - [Architecture](ARCHITECTURE.md)
   - [Development Guide](../DEVELOPMENT.md)
   - [API Documentation](http://localhost:8000/docs)

2. **Try Examples**
   - Create a multi-task workflow
   - Test retry logic
   - Monitor metrics in Grafana

3. **Extend the Platform**
   - Add custom task types
   - Implement authentication
   - Create custom dashboards

---

## Need Help?

- Check [PROJECT_STATUS.md](../PROJECT_STATUS.md) for current status
- Read [DEVELOPMENT.md](../DEVELOPMENT.md) for detailed dev guide
- See [ARCHITECTURE.md](ARCHITECTURE.md) for system design

---

Happy orchestrating! 🎉

