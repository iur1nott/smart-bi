# Dashboard Builder

A modern, clean architecture dashboard builder application that allows users to create professional dashboards from Excel data.

## Features

- **User Authentication**: Secure login and registration with JWT tokens
- **Excel Data Loading**: Support for XLSX and XLS file formats
- **Visualization Creation**: Multiple chart types including:
  - Bar charts
  - Line charts
  - Pie charts
  - Area charts
  - Scatter plots
  - Histograms
  - Box plots
  - Tables
  - Metric cards
- **Slide Management**: Organize visualizations in slides
- **Export Options**: Export to PDF, HTML, and LaTeX formats
- **PostgreSQL Integration**: Persistent storage for users and analyses
- **Docker Support**: Easy deployment with Docker Compose

## Architecture

This application follows Clean Architecture principles with:

- **Domain Layer**: Core business entities and value objects
- **Use Cases Layer**: Application services and business logic
- **Infrastructure Layer**: External services and implementations
- **Presentation Layer**: Streamlit UI components

## Installation

### Option 1: Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gurgel-bi.git
cd gurgel-bi
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
# Start PostgreSQL (adjust connection string as needed)
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/dashboard_builder"
```

5. Run the application:
```bash
streamlit run app.py
```

### Option 2: Docker

1. Clone the repository and navigate to it:
```bash
git clone https://github.com/yourusername/gurgel-bi.git
cd gurgel-bi
```

2. Create a `.env` file:
```bash
echo "JWT_SECRET_KEY=your-super-secret-key-change-in-production" > .env
```

3. Run with Docker Compose:
```bash
docker-compose up -d
```

4. Access the application at: http://localhost:8501

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/postgres` |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | `your-super-secret-key-change-in-production` |
| `SQL_ECHO` | Enable SQL query logging | `false` |

## Usage

1. **Register/Login**: Create an account or log in with existing credentials
2. **Create Analysis**: Click "Nova Análise" to start a new dashboard
3. **Upload Data**: Upload an Excel file (.xlsx or .xls)
4. **Add Visualizations**: Select chart types and configure them
5. **Organize Slides**: Add multiple slides to organize your dashboard
6. **Export**: Export your analysis to PDF, HTML, or LaTeX

## Project Structure

```
gurgel-bi/
├── app.py                 # Main application entry point
├── domain/               # Domain layer
│   ├── entities.py       # Business entities
│   ├── value_objects.py  # Value objects
│   └── repositories.py   # Repository interfaces
├── use_cases/            # Application services
│   ├── auth_service.py
│   ├── analysis_service.py
│   ├── data_service.py
│   └── export_service.py
├── infrastructure/       # External implementations
│   ├── database.py
│   ├── models.py
│   ├── auth/
│   ├── repositories/
│   ├── chart_factory.py
│   └── pdf_generator.py
├── presentation/         # UI components
│   ├── login.py
│   ├── sidebar.py
│   ├── canvas.py
│   ├── widget_palette.py
│   └── components.py
├── utils/               # Utility functions
├── data/                # Data storage
├── exports/             # Exported files
├── Dockerfile
├── docker-compose.yml
├── init.sql            # Database initialization
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black .
ruff check .
```

### Type Checking

```bash
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing UI framework
- [Polars](https://pola.rs/) for fast data processing
- [Plotly](https://plotly.com/) for interactive visualizations
- [SQLAlchemy](https://www.sqlalchemy.org/) for database abstraction
