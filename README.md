# 🚀 Distributed Task Orchestration Platform

> Production-grade платформа DisTorch для оркестрации распределенных задач в микросервисной архитектуре

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

---

## 📋 О проекте

**Distributed Task Orchestration Platform** — это продвинутый Airflow, специально заточенный под real-time обработку и микросервисы.

### Какую боль решает:
- ❌ Компании с 50+ микросервисами тонут в хаосе асинхронных задач
- ❌ Нет единой точки мониторинга и управления distributed workflows
- ❌ При падении одного сервиса теряется весь контекст выполнения
- ❌ Невозможно отследить, где именно застряла бизнес-транзакция

### Решение:
- ✅ Единая платформа для управления всеми распределенными задачами
- ✅ Real-time мониторинг и визуализация execution path
- ✅ Гарантии выполнения с автоматическими retry и компенсациями
- ✅ Отказоустойчивость и graceful degradation

---

## 🎯 Ключевые возможности

### 🔄 Workflow Management
- Декларативное описание многошаговых процессов
- Условное ветвление (if-else logic)
- Параллельное выполнение независимых задач
- Human-in-the-loop задачи

### 🛡️ Гарантии выполнения
- At-least-once delivery
- Автоматические retry с exponential backoff
- Dead Letter Queue для failed задач
- Компенсирующие транзакции (Saga pattern)

### 📊 Real-time мониторинг
- WebSocket подключения для live статусов
- Детальная телеметрия (latency, CPU, memory)
- Визуализация execution path
- Alerting при превышении SLA

### 💪 Отказоустойчивость
- Circuit Breaker для внешних сервисов
- Graceful degradation
- Автоматическое переназначение задач
- Checkpointing для длительных операций

---

## 🏗️ Архитектура

```
┌──────────────────────────────────────────────────────────────┐
│                        API Layer                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │ REST API   │  │ WebSocket  │  │ GraphQL    │             │
│  └────────────┘  └────────────┘  └────────────┘             │
└──────────────────────────────────────────────────────────────┘
                            │
┌──────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │Orchestrator│  │  Executor  │  │    Saga    │             │
│  └────────────┘  └────────────┘  └────────────┘             │
└──────────────────────────────────────────────────────────────┘
                            │
┌──────────────────────────────────────────────────────────────┐
│                      Domain Layer                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │  Workflow  │  │    Task    │  │ Execution  │             │
│  └────────────┘  └────────────┘  └────────────┘             │
└──────────────────────────────────────────────────────────────┘
                            │
┌──────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │ PostgreSQL │  │   Redis    │  │ RabbitMQ   │             │
│  └────────────┘  └────────────┘  └────────────┘             │
└──────────────────────────────────────────────────────────────┘
```

**Архитектурные паттерны:**
- 🏛️ Domain-Driven Design (DDD)
- 📡 Event-Driven Architecture
- 🔄 Saga Pattern (компенсирующие транзакции)
- 🔀 CQRS (разделение read/write)
- ⚡ Circuit Breaker
- 📝 Event Sourcing

---

## 🛠️ Tech Stack

| Категория | Технологии |
|-----------|-----------|
| **Backend** | Python 3.11+, FastAPI, Celery, Pydantic |
| **Databases** | PostgreSQL, Redis, ClickHouse, RabbitMQ |
| **Observability** | Prometheus, Grafana, OpenTelemetry, ELK |
| **DevOps** | Docker, Kubernetes, Terraform, GitHub Actions |

---

## 🚀 Quick Start

### Предварительные требования:
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Установка:

```bash
# Клонирование репозитория
git clone <repo-url>
cd distributed-task-orchestration-platform

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Запуск через Docker Compose
docker-compose up -d

# Применение миграций
python scripts/migrate.py

# Запуск приложения
uvicorn src.main:app --reload
```

Приложение будет доступно на `http://localhost:8000`

API документация: `http://localhost:8000/docs`

---

## 📚 Документация

- 📖 **[Обзор проекта](project-context/PROJECT_OVERVIEW.md)** — детальное описание проекта
- 🔄 **[Инструкции восстановления](project-context/RECOVERY_INSTRUCTIONS.md)** — алгоритм восстановления контекста
- ⚡ **[Quick Start Guide](project-context/QUICKSTART.md)** — быстрый старт

---

## 🔌 API Endpoints (основные)

### Workflow Management
```http
POST   /api/v1/workflows
GET    /api/v1/workflows/{workflow_id}
POST   /api/v1/workflows/{workflow_id}/cancel
POST   /api/v1/workflows/{workflow_id}/pause
POST   /api/v1/workflows/{workflow_id}/resume
```

### Task Operations
```http
POST   /api/v1/workflows/{workflow_id}/tasks
GET    /api/v1/tasks/{task_id}
POST   /api/v1/tasks/{task_id}/retry
POST   /api/v1/tasks/{task_id}/skip
```

### Real-time Updates
```http
WS     /ws/workflows/{workflow_id}
WS     /ws/tasks/stream
SSE    /api/v1/events/stream
```

### Analytics
```http
GET    /api/v1/analytics/performance
GET    /api/v1/analytics/bottlenecks
GET    /api/v1/analytics/cost
```

> Полная спецификация API доступна в Swagger UI: `/docs`

---

## 🧪 Тестирование

```bash
# Все тесты
pytest

# Unit тесты
pytest tests/unit/

# Integration тесты
pytest tests/integration/

# E2E тесты
pytest tests/e2e/

# С coverage
pytest --cov=src --cov-report=html
```

---

## 📊 Мониторинг

### Prometheus метрики
```
http://localhost:9090
```

### Grafana дашборды
```
http://localhost:3000
```

### Distributed tracing (Jaeger)
```
http://localhost:16686
```

---

## 🐳 Deployment

### Docker
```bash
docker build -t task-orchestrator:latest .
docker run -p 8000:8000 task-orchestrator:latest
```

### Kubernetes
```bash
kubectl apply -f deploy/kubernetes/
```

### Terraform
```bash
cd deploy/terraform
terraform init
terraform plan
terraform apply
```

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Автор

**DNTE**

- GitHub: here
- Email: nope)

---

## 🙏 Acknowledgments

- Inspired by Apache Airflow, Temporal, and Cadence
- Built with love using FastAPI and Python

---

**Status:** 🏗️ In Development  
**Version:** 0.1.1  
**Last Updated:** 2025-10-25

---

## 📖 Дополнительные ресурсы

- [System Design Documentation](docs/architecture/)
- [Architecture Decision Records](docs/architecture/ADR/)
- [Runbook](docs/runbook.md)
- [API Documentation](docs/api/)

---

Made with ❤️ for distributed systems engineers


