# Mezon IPS Bot

A production-ready FastAPI-based bot for [Mezon](https://mezon.vn) platform with expert management, program tracking, and interactive form capabilities. Built with modern Python async patterns and enterprise-grade architecture.

## Features

- **Mezon Integration** — Real-time message handling via [mezon-sdk](https://pypi.org/project/mezon-sdk/) with automatic reconnection
- **Expert Management** — Complete CRUD operations for expert profiles with search and filtering
- **Program/Contract Management** — Track programs, contracts, and project milestones
- **Interactive Forms** — Rich UI components (buttons, dropdowns, date pickers, text inputs) for seamless user interaction
- **Handler Architecture** — Pluggable command handlers with dependency injection
- **RESTful API** — FastAPI endpoints for health checks and bot status monitoring
- **Database Layer** — Async PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Production Ready** — Structured logging, error handling, and graceful shutdown

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Bot Commands](#bot-commands)
- [Architecture](#architecture)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Python 3.13+** — Modern async/await support
- **PostgreSQL 14+** — Database server
- **Mezon Account** — Bot credentials (Client ID and API Key)
- **Git** — Version control
- **uv** (recommended) or pip — Package management

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd mezon-ips-bot
```

### 2. Install dependencies

**Using uv (recommended):**
```bash
uv sync
```

**Using pip:**
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 4. Setup database

```bash
# Create database
createdb mezon_bot

# Run migrations
alembic upgrade head
```

### 5. Start the bot

```bash
python run.py --reload
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_ENV` | Yes | `dev` | Environment: `dev` or `prod` (dev enables OpenAPI docs) |
| `MEZON_CLIENT_ID` | Yes | - | Your Mezon bot client ID from [Mezon Developer Portal](https://mezon.vn) |
| `MEZON_API_KEY` | Yes | - | Your Mezon API key (keep secret!) |
| `DB_URI` | Yes | - | PostgreSQL connection string: `postgresql+asyncpg://user:pass@host:port/dbname` |
| `MEZON_BOT_REQUIRE_MENTION` | No | `false` | If `true`, bot only responds when mentioned (@Bot) |

### Getting Mezon Credentials

1. Visit [Mezon Developer Portal](https://mezon.vn)
2. Create a new bot application
3. Copy the **Client ID** and **API Key**
4. Add the bot to your Mezon server/channels

### Database Connection String Format

```
postgresql+asyncpg://username:password@hostname:port/database_name
```

**Examples:**
- Local: `postgresql+asyncpg://postgres:postgres@localhost:5432/mezon_bot`
- Docker: `postgresql+asyncpg://postgres:postgres@db:5432/mezon_bot`
- Cloud: `postgresql+asyncpg://user:pass@db.example.com:5432/mezon_bot`

## Database Setup

### Create Database

**Using psql:**
```bash
psql -U postgres
CREATE DATABASE mezon_bot;
\q
```

**Using createdb:**
```bash
createdb -U postgres mezon_bot
```

### Run Migrations

```bash
# Upgrade to latest schema
alembic upgrade head

# Check current version
alembic current

# View migration history
alembic history
```

### Create New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Review generated migration in alembic/versions/
# Then apply it
alembic upgrade head
```

## Running the Application

### Development Mode

```bash
# With auto-reload on code changes
python run.py --reload

# Custom host and port
python run.py --host 127.0.0.1 --port 8080 --reload
```

### Production Mode

```bash
# Single worker
python run.py --host 0.0.0.0 --port 8000

# Multiple workers (for high traffic)
python run.py --host 0.0.0.0 --port 8000 --workers 4
```

### Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address (use `127.0.0.1` for local only) |
| `--port` | `8000` | Port number |
| `--reload` | `False` | Auto-reload on code changes (dev only) |
| `--workers` | `1` | Number of worker processes |

### Application Startup Flow

1. **FastAPI Server** — Starts HTTP server
2. **Database Connection** — Establishes async PostgreSQL pool
3. **Mezon Login** — Authenticates bot with Mezon platform
4. **Handler Registration** — Loads and wires command handlers
5. **Message Listener** — Attaches to channel message events
6. **Ready** — Bot responds to commands in connected channels

## Deployment

### Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 8000

# Run migrations and start app
CMD alembic upgrade head && python run.py --host 0.0.0.0 --port 8000
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: mezon_bot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  bot:
    build: .
    depends_on:
      db:
        condition: service_healthy
    environment:
      APP_ENV: prod
      MEZON_CLIENT_ID: ${MEZON_CLIENT_ID}
      MEZON_API_KEY: ${MEZON_API_KEY}
      DB_URI: postgresql+asyncpg://postgres:postgres@db:5432/mezon_bot
      MEZON_BOT_REQUIRE_MENTION: false
    ports:
      - "8000:8000"
    restart: unless-stopped

volumes:
  postgres_data:
```

#### 3. Deploy with Docker Compose

```bash
# Create .env file with your credentials
echo "MEZON_CLIENT_ID=your_client_id" > .env
echo "MEZON_API_KEY=your_api_key" >> .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down
```

### VPS Deployment (Ubuntu/Debian)

#### 1. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.13
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install -y python3.13 python3.13-venv python3.13-dev

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Git
sudo apt install -y git
```

#### 2. Setup PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE mezon_bot;
CREATE USER mezon_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE mezon_bot TO mezon_user;
\q
```

#### 3. Clone and Configure

```bash
# Clone repository
git clone <repository-url> /opt/mezon-ips-bot
cd /opt/mezon-ips-bot

# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
nano .env  # Edit with your credentials
```

#### 4. Run Migrations

```bash
alembic upgrade head
```

#### 5. Create Systemd Service

Create `/etc/systemd/system/mezon-bot.service`:

```ini
[Unit]
Description=Mezon IPS Bot
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/mezon-ips-bot
Environment="PATH=/opt/mezon-ips-bot/.venv/bin"
ExecStart=/opt/mezon-ips-bot/.venv/bin/python run.py --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 6. Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service on boot
sudo systemctl enable mezon-bot

# Start service
sudo systemctl start mezon-bot

# Check status
sudo systemctl status mezon-bot

# View logs
sudo journalctl -u mezon-bot -f
```

### Nginx Reverse Proxy (Optional)

Create `/etc/nginx/sites-available/mezon-bot`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/mezon-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Cloud Platform Deployment

#### Railway

1. Create `railway.toml`:
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "alembic upgrade head && python run.py"
```

2. Deploy:
```bash
railway login
railway init
railway up
```

#### Heroku

1. Create `Procfile`:
```
release: alembic upgrade head
web: python run.py --host 0.0.0.0 --port $PORT
```

2. Deploy:
```bash
heroku create mezon-ips-bot
heroku addons:create heroku-postgresql:mini
git push heroku main
```

#### Render

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: mezon-ips-bot
    env: python
    buildCommand: pip install -e .
    startCommand: alembic upgrade head && python run.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.13.0
```

2. Connect repository to Render dashboard

## API Documentation

### Endpoints

#### Health Check
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-09T08:00:00Z"
}
```

#### Bot Status
```http
GET /api/v1/bot/status
```

**Response:**
```json
{
  "connected": true,
  "user_id": "123456789",
  "username": "MezonBot"
}
```

#### OpenAPI Schema (Development Only)
```http
GET /api/v1/openapi.json
```

Access interactive docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Bot Commands

### Expert Management

| Command | Description | Example |
|---------|-------------|---------|
| `*expert` | Show expert management help | `*expert` |
| `*expert list` | List all experts with pagination | `*expert list` |
| `*expert add` | Add new expert (interactive form) | `*expert add` |
| `*expert edit <cccd\|tên>` | Edit expert information | `*expert edit 012345678901` |
| `*expert delete <cccd\|tên>` | Delete expert | `*expert delete Nguyen Van A` |
| `*expert find name <tên>` | Search experts by name | `*expert find name Nguyen Van A` |
| `*expert find id <cccd>` | Search experts by CCCD | `*expert find id 012345678901` |

**Expert Fields:**
- Name (required)
- Email (required)
- Phone
- Expertise/Specialization
- Organization
- Bio/Description

### Program/Contract Management

| Command | Description | Example |
|---------|-------------|---------|
| `*program` | Show program management help | `*program` |
| `*program list` | List all programs | `*program list` |
| `*program add` | Add new program (interactive form) | `*program add` |
| `*program <code>` | Show program details by code | `*program PROJ-001` |
| `*program find <code>` | Find program by code | `*program find PRJ-001` |
| `*program edit <code>` | Edit program information | `*program edit PRJ-001` |
| `*program delete <code>` | Delete program | `*program delete PRJ-001` |
| `*contract expert list year <year>` | List expert contracts by year, newest first | `*contract expert list year 2026` |

**Program Fields:**
- Program Code (required, unique, auto-normalized to uppercase)
- Program Name (required)
- Activity Purpose
- Summary Activities
- End Date

**Contract Behaviors:**
- Program detail view includes button to list contracts in same project/program
- Contract numbers must be unique within same project
- Acceptance export is blocked after contract end date

### Interactive Forms

The bot uses rich interactive components:

- **Buttons** — Action triggers (Submit, Cancel, Delete)
- **Dropdowns** — Select from predefined options
- **Date Pickers** — Calendar-based date selection
- **Text Inputs** — Single-line and multi-line text fields

**Example Flow:**
1. User types `*expert add`
2. Bot displays interactive form with input fields
3. User fills form and clicks Submit
4. Bot validates and saves data
5. Bot confirms success or shows validation errors

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Mezon Platform                       │
│                    (WebSocket Connection)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Lifespan Manager                         │  │
│  │  • Mezon Login/Logout                                 │  │
│  │  • Database Connection Pool                           │  │
│  │  • Handler Registration                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Handler Manager                          │  │
│  │  • Route messages to handlers                         │  │
│  │  • Command parsing                                    │  │
│  │  • Error handling                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Message Handlers                         │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │   Expert   │  │  Program   │  │    LLM     │     │  │
│  │  │  Handler   │  │  Handler   │  │  Handler   │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Service Layer                            │  │
│  │  • Business Logic                                     │  │
│  │  • Data Validation                                    │  │
│  │  • External API Integration                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Repository Layer                         │  │
│  │  • Database Operations (CRUD)                         │  │
│  │  • Query Building                                     │  │
│  │  • Transaction Management                             │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│  • Experts Table                                             │
│  • Programs Table                                            │
│  • Alembic Migrations                                        │
└─────────────────────────────────────────────────────────────┘
```

### Project Structure

```
mezon-ips-bot/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── bot.py              # Bot status endpoints
│   │       └── health.py           # Health check endpoints
│   │
│   ├── core/
│   │   └── settings/
│   │       ├── __init__.py
│   │       └── app_settings.py     # Pydantic settings (env vars)
│   │
│   ├── database/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── expert.py           # Expert SQLAlchemy model
│   │   │   └── program.py          # Program SQLAlchemy model
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── expert_repository.py
│   │   │   └── program_repository.py
│   │   ├── __init__.py
│   │   └── connect.py              # Async database connection
│   │
│   ├── dependencies/
│   │   ├── __init__.py
│   │   └── container.py            # Dependency injection container
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── expert.py               # Expert Pydantic schemas
│   │   └── program.py              # Program Pydantic schemas
│   │
│   ├── services/
│   │   ├── bot/
│   │   │   ├── handlers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_message_handler.py
│   │   │   │   ├── expert_handler.py
│   │   │   │   ├── program_handler.py
│   │   │   │   └── llm_handler.py
│   │   │   ├── __init__.py
│   │   │   └── handler_manager.py  # Routes messages to handlers
│   │   │
│   │   ├── expert/
│   │   │   ├── __init__.py
│   │   │   └── expert_service.py   # Expert business logic
│   │   │
│   │   ├── program/
│   │   │   ├── __init__.py
│   │   │   └── program_service.py  # Program business logic
│   │   │
│   │   └── llm/
│   │       ├── __init__.py
│   │       └── llm_service.py      # LLM integration
│   │
│   └── main.py                     # FastAPI app + lifespan
│
├── alembic/
│   ├── versions/                   # Database migrations
│   ├── env.py
│   └── script.py.mako
│
├── .env.example                    # Environment template
├── .gitignore
├── alembic.ini                     # Alembic configuration
├── pyproject.toml                  # Project metadata + dependencies
├── run.py                          # CLI entry point (uvicorn)
└── README.md
```

### Design Patterns

#### 1. Dependency Injection
- Uses `dependency-injector` for IoC container
- Services, repositories, and handlers are wired automatically
- Enables easy testing and loose coupling

#### 2. Repository Pattern
- Abstracts database operations
- Repositories handle CRUD operations
- Services contain business logic

#### 3. Handler Pattern
- Each command has a dedicated handler
- Handlers extend `BaseMessageHandler`
- Handler Manager routes messages to appropriate handler

#### 4. Service Layer
- Business logic separated from handlers
- Services orchestrate repositories and external APIs
- Reusable across different interfaces (bot, API, CLI)

### Data Flow

```
User Message → Mezon Platform → Handler Manager → Specific Handler
                                                         ↓
                                                    Service Layer
                                                         ↓
                                                   Repository Layer
                                                         ↓
                                                      Database
                                                         ↓
                                                    Response ← ← ← ←
```

### Database Schema

#### Experts Table
```sql
CREATE TABLE experts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    expertise TEXT,
    organization VARCHAR(255),
    bio TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Programs Table
```sql
CREATE TABLE programs (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    budget DECIMAL(15, 2),
    status VARCHAR(50) DEFAULT 'Planning',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd mezon-ips-bot

# Install dependencies with uv
uv sync

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Setup pre-commit hooks (optional)
pre-commit install
```

### Code Quality Tools

#### Linting and Formatting

```bash
# Check code style
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Check types (if using mypy)
mypy app/
```

#### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_expert_service.py

# Run with verbose output
pytest -v
```

### Database Migrations

#### Create Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "add user table"

# Create empty migration
alembic revision -m "custom migration"
```

#### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade abc123

# Downgrade one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade abc123
```

#### Migration History

```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

### Adding a New Command Handler

#### 1. Create Handler Class

Create `app/services/bot/handlers/my_handler.py`:

```python
from app.services.bot.handlers.base_message_handler import BaseMessageHandler
from mezon import ChannelMessage

class MyHandler(BaseMessageHandler):
    def get_command(self) -> str:
        return "*mycommand"
    
    async def handle(self, message: ChannelMessage, content: str) -> None:
        # Your logic here
        await self.reply_message(
            message=message,
            content="Hello from my handler!"
        )
```

#### 2. Register in Container

Edit `app/dependencies/container.py`:

```python
from app.services.bot.handlers.my_handler import MyHandler

class Container(containers.DeclarativeContainer):
    # ... existing code ...
    
    # Add your handler
    my_handler = providers.Singleton(
        MyHandler,
        mezon_client=mezon_client,
    )
    
    # Add to handler list
    handler_manager = providers.Singleton(
        HandlerManager,
        handlers=providers.List(
            expert_handler,
            program_handler,
            my_handler,  # Add here
        ),
    )
```

#### 3. Test Your Handler

```bash
# Restart the bot
python run.py --reload

# In Mezon channel, type:
*mycommand
```

### Adding Interactive Forms

Use `InteractiveBuilder` and `ButtonBuilder`:

```python
from mezon import InteractiveBuilder, ButtonBuilder, InputTextBuilder

# Create form
interactive = InteractiveBuilder()
interactive.add_component(
    InputTextBuilder()
    .set_id("name_input")
    .set_label("Name")
    .set_placeholder("Enter your name")
    .set_required(True)
    .build()
)
interactive.add_component(
    ButtonBuilder()
    .set_id("submit_btn")
    .set_label("Submit")
    .set_style(1)  # Primary button
    .build()
)

# Send form
await self.send_message(
    channel_id=message.channel_id,
    content="Please fill the form:",
    interactive=interactive.build()
)
```

### Environment-Specific Configuration

#### Development (.env)
```bash
APP_ENV=dev
MEZON_CLIENT_ID=your_dev_client_id
MEZON_API_KEY=your_dev_api_key
DB_URI=postgresql+asyncpg://postgres:postgres@localhost:5432/mezon_bot_dev
```

#### Production (.env.prod)
```bash
APP_ENV=prod
MEZON_CLIENT_ID=your_prod_client_id
MEZON_API_KEY=your_prod_api_key
DB_URI=postgresql+asyncpg://user:pass@prod-db:5432/mezon_bot
MEZON_BOT_REQUIRE_MENTION=true
```

### Debugging

#### Enable Debug Logging

```python
# In app/main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format=’%(asctime)s - %(name)s - %(levelname)s - %(message)s’
)
```

#### Debug Database Queries

```python
# In app/database/connect.py
engine = create_async_engine(
    settings.db_uri,
    echo=True,  # Enable SQL query logging
)
```

#### Debug Mezon Messages

```python
# In handler
async def handle(self, message: ChannelMessage, content: str) -> None:
    print(f"Received message: {message}")
    print(f"Content: {content}")
    print(f"Channel ID: {message.channel_id}")
    print(f"User ID: {message.sender_id}")
```

### Performance Optimization

#### Database Connection Pooling

```python
# In app/database/connect.py
engine = create_async_engine(
    settings.db_uri,
    pool_size=20,          # Max connections
    max_overflow=10,       # Extra connections when pool full
    pool_pre_ping=True,    # Verify connections before use
    pool_recycle=3600,     # Recycle connections after 1 hour
)
```

#### Async Best Practices

```python
# Use async/await consistently
async def fetch_data():
    async with session.begin():
        result = await session.execute(query)
        return result.scalars().all()

# Batch operations
async def batch_insert(items: list):
    async with session.begin():
        session.add_all(items)
        await session.commit()
```

### Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes and test thoroughly
4. Run linting: `ruff check . && ruff format .`
5. Commit changes: `git commit -m "feat: add my feature"`
6. Push to branch: `git push origin feature/my-feature`
7. Create Pull Request

#### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `refactor:` — Code refactoring
- `test:` — Adding tests
- `chore:` — Maintenance tasks

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Error:** `asyncpg.exceptions.InvalidCatalogNameError: database "mezon_bot" does not exist`

**Solution:**
```bash
# Create database
createdb mezon_bot

# Or using psql
psql -U postgres -c "CREATE DATABASE mezon_bot;"
```

#### 2. Mezon Authentication Failed

**Error:** `MezonError: Invalid credentials`

**Solution:**
- Verify `MEZON_CLIENT_ID` and `MEZON_API_KEY` in `.env`
- Check credentials at [Mezon Developer Portal](https://mezon.vn)
- Ensure bot is added to your Mezon server

#### 3. Migration Failed

**Error:** `alembic.util.exc.CommandError: Target database is not up to date`

**Solution:**
```bash
# Check current version
alembic current

# Stamp database to current version (if needed)
alembic stamp head

# Run migrations
alembic upgrade head
```

#### 4. Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
python run.py --port 8001
```

#### 5. Module Import Errors

**Error:** `ModuleNotFoundError: No module named ‘app’`

**Solution:**
```bash
# Reinstall in editable mode
pip install -e .

# Or ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 6. Bot Not Responding

**Checklist:**
- [ ] Bot is running: `systemctl status mezon-bot` or check logs
- [ ] Bot is connected: Check `GET /api/v1/bot/status`
- [ ] Bot is in the channel
- [ ] Command syntax is correct (e.g., `*expert list`)
- [ ] Check logs for errors: `journalctl -u mezon-bot -f`

#### 7. Interactive Forms Not Working

**Solution:**
- Ensure Mezon SDK version supports interactive components
- Check form validation in handler
- Verify button IDs match in handler logic

### Getting Help

- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-repo/discussions)
- **Mezon SDK:** [mezon-sdk Documentation](https://pypi.org/project/mezon-sdk/)

### Logs Location

- **Development:** Console output
- **Production (systemd):** `journalctl -u mezon-bot -f`
- **Docker:** `docker-compose logs -f bot`
- **Application logs:** Configure in `app/main.py`

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- [Mezon Platform](https://mezon.vn) — Chat platform
- [FastAPI](https://fastapi.tiangolo.com/) — Web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM
- [Alembic](https://alembic.sqlalchemy.org/) — Database migrations
- [dependency-injector](https://python-dependency-injector.ets-labs.org/) — DI container
