# Dashboard Builder

A professional Streamlit application for building dashboards from Excel data, built with Clean Architecture principles.

## Features

- **📊 Data Visualization**: Multiple chart types (bar, line, pie, scatter, heatmap, etc.)
- **📋 Interactive Tables**: Sortable and filterable data tables
- **💬 Comments**: Add comments to visualizations
- **📄 Export**: LaTeX to PDF export with professional formatting
- **🔐 Authentication**: Secure user authentication with JWT
- **💾 Persistence**: PostgreSQL database for user data and history

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/dashboard-builder.git
cd dashboard-builder

# Copy environment file
cp .env.example .env

# Start development environment
docker-compose --profile dev up

# Or start production environment
docker-compose --profile prod up
```

### Using UV (Local Development)

[UV](https://docs.astral.sh/uv/) is a fast Python package manager that replaces pip, pip-tools, and virtualenv.

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# Install development dependencies
uv sync --dev

# Run the application
streamlit run app.py
```

## Project Structure

```
dashboard_builder/
├── app.py                    # Main application entry point
├── pyproject.toml            # Project configuration (UV/pip)
├── uv.lock                   # Locked dependencies
├── Dockerfile                # Production Docker image
├── Dockerfile.dev            # Development Docker image
├── docker-compose.yml        # Docker services configuration
│
├── domain/                   # Domain Layer (Pure Business Logic)
│   ├── entities.py           # Core business entities
│   ├── value_objects.py      # Immutable value objects
│   └── repositories.py       # Repository interfaces
│
├── use_cases/                # Use Cases Layer (Application Logic)
│   ├── auth_service.py       # Authentication operations
│   ├── analysis_service.py   # Analysis management
│   ├── data_service.py       # Data processing
│   └── export_service.py     # Export operations
│
├── infrastructure/           # Infrastructure Layer
│   ├── database.py           # PostgreSQL connection
│   ├── models.py             # SQLAlchemy models
│   ├── repositories/         # Repository implementations
│   ├── auth/                 # JWT and password handling
│   └── chart_factory.py      # Chart generation
│
├── presentation/             # Presentation Layer (Streamlit UI)
│   ├── login.py              # Authentication UI
│   ├── sidebar.py            # Main navigation
│   ├── widget_palette.py     # Visualization widgets
│   ├── canvas.py             # Slide editing
│   └── components.py         # UI components
│
├── .streamlit/
│   └── config.toml           # Streamlit configuration
│
├── data/                     # Persistent data storage
├── download/                 # Generated exports
└── tests/                    # Test suite
```

## Architecture

The application follows Clean Architecture principles:

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│    Streamlit UI components, dialogs, and navigation            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      USE CASES LAYER                            │
│    Business logic and application services                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DOMAIN LAYER                              │
│    Pure business entities, value objects, and interfaces        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                          │
│    PostgreSQL, SQLAlchemy, JWT, external integrations           │
└─────────────────────────────────────────────────────────────────┘
```

## Development

### Running Tests

```bash
# With UV
uv run pytest

# With coverage
uv run pytest --cov=domain --cov=use_cases --cov-report=html
```

### Code Quality

```bash
# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy domain/ use_cases/ infrastructure/ presentation/

# Linting
uv run ruff check .
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Required |
| `POSTGRES_USER` | PostgreSQL username | `dashboard_user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | Required |
| `POSTGRES_DB` | Database name | `dashboard_builder` |

## Docker Profiles

### Development Profile
```bash
docker-compose --profile dev up
```
- Hot reload enabled
- pgAdmin available at port 5050
- Source mounted as volume

### Production Profile
```bash
docker-compose --profile prod up
```
- Optimized build
- No development tools
- Minimal image size

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request
