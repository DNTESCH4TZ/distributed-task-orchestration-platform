# 🏛️ Architecture Overview

> Архитектурное описание Task Orchestrator Platform

---

## 📐 Архитектурный стиль

Проект использует **Domain-Driven Design (DDD)** с **Clean Architecture** принципами.

### Слои архитектуры

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ REST API    │  │ WebSocket   │  │ GraphQL     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Use Cases   │  │  Services   │  │     DTOs    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Entities   │  │ Value Objs  │  │ Repos (if)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Database   │  │    Redis    │  │  RabbitMQ   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Domain Layer

### Entities (Aggregate Roots)

**Workflow**
- Управляет DAG задач
- Контролирует жизненный цикл выполнения
- Валидирует зависимости (нет циклов)

**Task**
- Единица выполнения работы
- Управляет retry логикой
- Хранит payload и result

### Value Objects

**TaskStatus**, **WorkflowStatus**
- Иммутабельные
- Содержат бизнес-логику для переходов

**RetryPolicy**
- Конфигурация retry стратегии
- Exponential backoff логика

**TaskConfig**
- Конфигурация выполнения задачи
- Timeout, priority, idempotency

---

## 🔄 Event-Driven Architecture

### Domain Events

События публикуются при изменении состояния:

```python
WorkflowStarted -> TaskQueued -> TaskStarted -> TaskCompleted -> WorkflowCompleted
```

### Event Flow

```
1. Domain Entity изменяет состояние
2. Публикует Domain Event
3. Event Handler реагирует
4. Может триггерить другие события
```

---

## 🗄️ Data Flow (CQRS)

### Write Model (Commands)

```
API → Use Case → Domain Entity → Repository → PostgreSQL
```

### Read Model (Queries)

```
API → Query Service → Read Replica / Cache → Response
```

**Оптимизации:**
- Read replica для аналитики
- Redis cache для hot data
- ClickHouse для исторических данных

---

## 🔁 Saga Pattern для Distributed Transactions

### Orchestration-based Saga

```
Workflow (Orchestrator)
  ├─ Task 1 → Success → Task 2
  ├─ Task 2 → Failure → Compensation 1
  └─ Compensation 1 → WorkflowCompensated
```

### Compensation Tasks

Каждая задача может иметь `compensation_task_id`:
- Если задача N fails → запускается компенсация для задач 1..N-1
- Гарантирует консистентность в распределенной системе

---

## ⚡ Performance Optimizations (1M RPS)

### 1. Async все the way

```python
# Async database
engine = create_async_engine(...)
async with AsyncSession() as session:
    await session.execute(...)

# Async Redis
async with redis.Redis() as r:
    await r.get(...)
```

### 2. Connection Pooling

```python
# Database: 20 connections + 10 overflow per worker
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis: 50 connections per pool
REDIS_MAX_CONNECTIONS=50
```

### 3. Batching

```python
# Batch inserts
await repository.save_many(tasks)

# Batch reads
tasks = await repository.get_many(task_ids)
```

### 4. Caching Strategy

```
L1: In-memory (LRU cache)
L2: Redis (hot data, TTL=60s)
L3: PostgreSQL read replica
L4: PostgreSQL primary
```

### 5. Fast Serialization

```python
# ORJSON вместо json (2-5x faster)
from fastapi.responses import ORJSONResponse

# MsgPack для Celery (compact + fast)
CELERY_TASK_SERIALIZER=msgpack
```

### 6. uvloop + httptools

```python
# 2-4x faster event loop
import uvloop
uvloop.install()

# Faster HTTP parsing
uvicorn.run(..., loop="uvloop", http="httptools")
```

---

## 🛡️ Resilience Patterns

### 1. Circuit Breaker

```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(
    fail_max=5,  # Open after 5 failures
    timeout_duration=60,  # Stay open for 60s
)

@breaker
async def call_external_api():
    ...
```

### 2. Retry with Exponential Backoff

```python
from tenacity import retry, wait_exponential

@retry(wait=wait_exponential(multiplier=1, min=1, max=60))
async def unreliable_operation():
    ...
```

### 3. Graceful Degradation

```python
try:
    result = await analytics_service.get_insights()
except ServiceUnavailable:
    result = cached_insights  # Fallback to cache
```

### 4. Bulkhead Pattern

```python
# Separate connection pools
write_engine = create_async_engine(..., pool_size=20)
read_engine = create_async_engine(..., pool_size=10)
```

---

## 📊 Observability

### 3 Pillars

**1. Metrics (Prometheus)**
```python
from prometheus_client import Counter, Histogram

task_executions = Counter('task_executions_total', 'Total tasks executed')
task_duration = Histogram('task_duration_seconds', 'Task duration')
```

**2. Logs (Structured Logging)**
```python
import structlog

logger = structlog.get_logger()
logger.info("task_started", task_id=task.id, workflow_id=workflow.id)
```

**3. Traces (OpenTelemetry → Jaeger)**
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("execute_task"):
    ...
```

---

## 🔐 Security

### 1. Authentication & Authorization

- JWT tokens с expiration
- Role-based access control (RBAC)
- API key для service-to-service

### 2. Input Validation

- Pydantic для всех inputs
- SQL injection защита (SQLAlchemy)
- XSS защита (FastAPI auto-escaping)

### 3. Rate Limiting

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/workflows")
@limiter.limit("100/minute")
async def get_workflows():
    ...
```

### 4. Secrets Management

- Environment variables (12-factor app)
- HashiCorp Vault для production
- Encrypted secrets in K8s

---

## 🚀 Scalability

### Horizontal Scaling

```
                    Load Balancer
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    API Node 1      API Node 2       API Node 3
        │                │                │
        └────────────────┼────────────────┘
                         │
                  Shared State Layer
                  (PostgreSQL + Redis)
```

### Sharding Strategy

**Database Sharding:**
- По `workflow_id` hash
- Consistent hashing для равномерного распределения

**Task Distribution:**
- Celery workers по типу задач
- Priority queues

---

## 📈 Trade-offs

### CAP Theorem

**Выбор: CP (Consistency + Partition Tolerance)**

- Используем PostgreSQL (ACID гарантии)
- Strong consistency для workflow state
- Eventual consistency для analytics

### Performance vs Consistency

- Write: сильная консистентность (PostgreSQL)
- Read: eventual consistency OK (cache, read replica)

### Complexity vs Maintainability

- DDD: больше кода, но лучше структура
- Event-Driven: асинхронность, но сложнее debugging

---

## 🔮 Future Improvements

1. **Multi-region deployment** - географическая репликация
2. **GraphQL API** - гибкие запросы
3. **Machine Learning** - предсказание bottlenecks
4. **WebAssembly tasks** - безопасное выполнение user code
5. **Time-series DB** - Prometheus долгосрочное хранение

---

**Last updated:** 2025-10-21

